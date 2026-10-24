interface Window {
  racTheme: {
    get(): string | null;
    set(choice: "light" | "dark" | null): void;
  };
}
