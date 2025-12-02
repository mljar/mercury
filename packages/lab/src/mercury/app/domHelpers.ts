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

/** Hide error outputs inside an OutputArea DOM node (Mercury-only view). */
export function hideErrorOutputs(node: HTMLElement): void {
  // Kilka typowych selektorów dla errorów w JupyterLab
  const errorNodes = node.querySelectorAll<HTMLElement>(
    [
      '.jp-OutputArea-output.jp-mod-error',
      '.jp-OutputArea-output[data-mime-type="application/vnd.jupyter.stderr"]',
      '.jp-OutputArea-output[data-mime-type="application/vnd.jupyter.error"]'
    ].join(',')
  );

  errorNodes.forEach(el => {
    // Możesz też użyć el.remove(), ale display:none jest łagodniejsze dla layoutu
    el.style.display = 'none';
  });
}

/**
 * Hide error outputs when an OutputArea mutates.
 * Returns the observer so callers may disconnect if desired.
 */
export function hideErrorOutputsOnChange(node: HTMLElement): MutationObserver {
  const hide = () => {
    hideErrorOutputs(node);
  };

  // od razu sprzątamy stan początkowy
  hide();

  const observer = new MutationObserver(hide);
  observer.observe(node, { childList: true, subtree: true });
  return observer;
}
