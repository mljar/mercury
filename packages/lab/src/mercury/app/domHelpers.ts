/** Remove descendants by className from an HTMLElement. */
export function removeElements(node: HTMLElement, className: string): void {
  const elements = node.getElementsByClassName(className);
  for (let i = 0; i < elements.length; i++) {
    elements[i].remove();
  }
}

/**
 * Remove prompts when output area mutates.
 * Returns the observer so callers may disconnect if desired.
 */
export function removePromptsOnChange(node: HTMLElement): MutationObserver {
  const remove = () => {
    removeElements(node, 'jp-OutputPrompt');
    removeElements(node, 'jp-OutputArea-promptOverlay');
  };
  remove();
  const observer = new MutationObserver(remove);
  observer.observe(node, { childList: true, subtree: true });
  return observer;
}
