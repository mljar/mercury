/** Remove descendants by className from an HTMLElement. */
export function removeElements(node: HTMLElement, className: string): void {
  const elements = Array.from(node.getElementsByClassName(className));
  for (const el of elements) {
    el.remove();
  }
}

/**
 * Remove prompts when output area mutates.
 * Optional `onChange` callback is called after DOM cleanup.
 * Returns the observer so callers may disconnect if desired.
 */
export function removePromptsOnChange(
  node: HTMLElement,
  onChange?: () => void
): MutationObserver {
  const remove = () => {
    removeElements(node, 'jp-OutputPrompt');
    removeElements(node, 'jp-OutputArea-promptOverlay');
    if (onChange) {
      onChange();
    }
  };
  remove();
  const observer = new MutationObserver(remove);
  observer.observe(node, { childList: true, subtree: true });
  return observer;
}
