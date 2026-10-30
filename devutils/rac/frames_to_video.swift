#!/usr/bin/env swift

// Copyright 2026 The rac Authors
// You can use, redistribute, and/or modify this source code under
// the terms of the GPL-3.0 license that can be found in the LICENSE file.

// Turns a PNG sequence from the dev harness (burst or record) into an H.264
// .mp4 with AVFoundation, since ffmpeg isn't installed on the build Macs.
//
// usage: swift devutils/rac/frames_to_video.swift [options] <dir|list.txt> <out.mp4>
//   <dir>         every *.png in it, in name order (f00.png, f01.png, ...)
//   <list.txt>    one PNG path per line, one video frame each; repeat a path
//                 to hold a frame (for frames resampled onto a fixed clock)
//   --fps N       frames per second of the input (default 60)
//   --slow K      also write <out>-<K>x.mp4, K times slower (e.g. 4)
//   --scale S     scale each frame by S (default 1; 0.5 halves a 2x capture)
//
// Every frame is drawn onto an opaque background, so transparent window
// corners come out black rather than undefined.

import AVFoundation
import CoreGraphics
import Foundation
import ImageIO

struct Options {
  var input = ""
  var output = ""
  var fps = 60
  var slow = 0
  var scale = 1.0
}

func fail(_ message: String) -> Never {
  FileHandle.standardError.write(("frames_to_video: " + message + "\n").data(using: .utf8)!)
  exit(1)
}

func parseOptions() -> Options {
  var options = Options()
  var positional: [String] = []
  var args = CommandLine.arguments.dropFirst()
  while let arg = args.popFirst() {
    switch arg {
    case "--fps":
      guard let value = args.popFirst().flatMap(Int.init), value > 0 else { fail("--fps needs a number") }
      options.fps = value
    case "--slow":
      guard let value = args.popFirst().flatMap(Int.init), value > 1 else { fail("--slow needs a number above 1") }
      options.slow = value
    case "--scale":
      guard let value = args.popFirst().flatMap(Double.init), value > 0 else { fail("--scale needs a number") }
      options.scale = value
    default:
      positional.append(arg)
    }
  }
  guard positional.count == 2 else {
    fail("usage: frames_to_video.swift [--fps N] [--slow K] [--scale S] <dir|list.txt> <out.mp4>")
  }
  options.input = positional[0]
  options.output = positional[1]
  return options
}

func framePaths(_ input: String) -> [String] {
  var isDirectory: ObjCBool = false
  guard FileManager.default.fileExists(atPath: input, isDirectory: &isDirectory) else {
    fail("no such file or folder: \(input)")
  }
  if isDirectory.boolValue {
    let names = (try? FileManager.default.contentsOfDirectory(atPath: input)) ?? []
    return names.filter { $0.hasSuffix(".png") }.sorted().map { (input as NSString).appendingPathComponent($0) }
  }
  guard let text = try? String(contentsOfFile: input, encoding: .utf8) else { fail("can't read \(input)") }
  let base = (input as NSString).deletingLastPathComponent
  return text.split(separator: "\n").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
    .map { $0.hasPrefix("/") ? $0 : (base as NSString).appendingPathComponent($0) }
}

func loadImage(_ path: String) -> CGImage {
  guard let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
    let image = CGImageSourceCreateImageAtIndex(source, 0, nil)
  else { fail("can't read image \(path)") }
  return image
}

func writeVideo(frames: [String], to output: String, fps: Int, frameDuration: CMTime, scale: Double) {
  let first = loadImage(frames[0])
  // H.264 wants even dimensions.
  let width = Int((Double(first.width) * scale).rounded()) & ~1
  let height = Int((Double(first.height) * scale).rounded()) & ~1
  let url = URL(fileURLWithPath: output)
  try? FileManager.default.removeItem(at: url)
  guard let writer = try? AVAssetWriter(outputURL: url, fileType: .mp4) else { fail("can't write \(output)") }
  let input = AVAssetWriterInput(
    mediaType: .video,
    outputSettings: [
      AVVideoCodecKey: AVVideoCodecType.h264,
      AVVideoWidthKey: width,
      AVVideoHeightKey: height,
      AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: max(4_000_000, width * height * 6),
        AVVideoExpectedSourceFrameRateKey: fps,
        AVVideoMaxKeyFrameIntervalKey: fps,
      ],
    ])
  input.expectsMediaDataInRealTime = false
  let adaptor = AVAssetWriterInputPixelBufferAdaptor(
    assetWriterInput: input,
    sourcePixelBufferAttributes: [
      kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
      kCVPixelBufferWidthKey as String: width,
      kCVPixelBufferHeightKey as String: height,
    ])
  writer.add(input)
  guard writer.startWriting() else { fail("can't start writing: \(writer.error?.localizedDescription ?? "?")") }
  writer.startSession(atSourceTime: .zero)

  for (index, path) in frames.enumerated() {
    while !input.isReadyForMoreMediaData { Thread.sleep(forTimeInterval: 0.005) }
    guard let pool = adaptor.pixelBufferPool else { fail("no pixel buffer pool") }
    var buffer: CVPixelBuffer?
    CVPixelBufferPoolCreatePixelBuffer(nil, pool, &buffer)
    guard let pixels = buffer else { fail("can't make a pixel buffer") }
    CVPixelBufferLockBaseAddress(pixels, [])
    let context = CGContext(
      data: CVPixelBufferGetBaseAddress(pixels), width: width, height: height, bitsPerComponent: 8,
      bytesPerRow: CVPixelBufferGetBytesPerRow(pixels), space: CGColorSpace(name: CGColorSpace.sRGB)!,
      bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)!
    context.setFillColor(CGColor(gray: 0, alpha: 1))
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.interpolationQuality = .high
    context.draw(loadImage(path), in: CGRect(x: 0, y: 0, width: width, height: height))
    CVPixelBufferUnlockBaseAddress(pixels, [])
    let time = CMTimeMultiply(frameDuration, multiplier: Int32(index))
    if !adaptor.append(pixels, withPresentationTime: time) {
      fail("can't add frame \(path): \(writer.error?.localizedDescription ?? "?")")
    }
  }
  input.markAsFinished()
  // Hold the last frame for its full duration.
  writer.endSession(atSourceTime: CMTimeMultiply(frameDuration, multiplier: Int32(frames.count)))
  let done = DispatchSemaphore(value: 0)
  writer.finishWriting { done.signal() }
  done.wait()
  guard writer.status == .completed else { fail("writing failed: \(writer.error?.localizedDescription ?? "?")") }
  print("wrote \(output) (\(frames.count) frames, \(width)x\(height))")
}

let options = parseOptions()
let frames = framePaths(options.input)
guard !frames.isEmpty else { fail("no PNGs in \(options.input)") }
let frameDuration = CMTime(value: 1, timescale: CMTimeScale(options.fps))
writeVideo(frames: frames, to: options.output, fps: options.fps, frameDuration: frameDuration, scale: options.scale)
if options.slow > 1 {
  let slowOutput = (options.output as NSString).deletingPathExtension + "-\(options.slow)x.mp4"
  writeVideo(
    frames: frames, to: slowOutput, fps: options.fps,
    frameDuration: CMTime(value: CMTimeValue(options.slow), timescale: CMTimeScale(options.fps)), scale: options.scale)
}
