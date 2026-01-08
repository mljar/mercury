import { ToolbarButton } from '@jupyterlab/apputils';

import { DocumentRegistry } from '@jupyterlab/docregistry';

import { NotebookPanel, INotebookModel } from '@jupyterlab/notebook';

import { CommandRegistry } from '@lumino/commands';

import { IDisposable } from '@lumino/disposable';

import { Widget } from '@lumino/widgets';

/**
 * A WidgetExtension for Notebook's toolbar to open a `Mercury` widget.
 */
export class OpenMercuryButton
  implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel>
{
  /**
   * Instantiate a new NotebookButton.
   * @param commands The command registry.
   */
  constructor(commands: CommandRegistry) {
    this._commands = commands;
  }

  /**
   * Create a new extension object.
   */
  createNew(panel: NotebookPanel): IDisposable {
    const button = new ToolbarButton({
      tooltip: 'Open with Mercury',
      iconClass: 'mrc-Icon',
      onClick: () => {
        this._commands
          .execute('docmanager:open', {
            path: panel.context.path,
            factory: 'Mercury',
            options: {
              mode: 'split-right',
              ref: panel.id
            }
          })
          .then(widget => {
            if (widget instanceof Widget) {
              panel.content.disposed.connect(() => {
                widget.dispose();
              });
            }
          });
      }
    });
    panel.toolbar.insertItem(0, 'open-mercury', button);
    return button;
  }

  private _commands: CommandRegistry;
}
