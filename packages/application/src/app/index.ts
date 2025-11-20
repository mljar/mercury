import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { createRendermimePlugins } from '@jupyterlab/application/lib/mimerenderers';
import { PageConfig } from '@jupyterlab/coreutils';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { IRenderMime } from '@jupyterlab/rendermime-interfaces';
import { Token } from '@lumino/coreutils';
import { Message } from '@lumino/messaging';
import { Signal, ISignal } from '@lumino/signaling';
import { BoxLayout, Widget } from '@lumino/widgets';

/**
 * The Mercury application shell token.
 */
export const IMercuryShell = new Token<MercuryShell>(
  'mercury-application:IMercuryShell'
);

export class MercuryShell extends Widget implements JupyterFrontEnd.IShell {
  constructor() {
    super();
    this._updated = new Signal(this);
    this.layout = new BoxLayout();
    this.id = 'main';
    this._currentWidget = null;
  }

  /**
   * Signal emitted when the shell is updated.
   */
  get updated(): ISignal<MercuryShell, void> {
    return this._updated;
  }

  /**
   * Activates a widget inside the application shell.
   *
   * @param id - The ID of the widget being activated.
   */
  activateById(id: string): void {
    // pass no-op
  }

  /**
   * Add a widget to the application shell.
   *
   * @param widget - The widget being added.
   *
   * @param area - Optional region in the shell into which the widget should
   * be added.
   *
   * @param options - Optional flags the shell might use when opening the
   * widget, as defined in the `DocumentRegistry`.
   */
  add(
    widget: Widget,
    area?: string,
    options?: DocumentRegistry.IOpenOptions
  ): void {
    if ((this.layout as BoxLayout).widgets.length > 0 || area !== 'mercury') {
      // Bail
      return;
    }
    BoxLayout.setStretch(widget, 1);
    (this.layout as BoxLayout).addWidget(widget);
    this._currentWidget = widget;
  }
  /**
   * The focused widget in the application shell.
   *
   * #### Notes
   * Different shell implementations have latitude to decide what "current"
   * or "focused" mean, depending on their user interface characteristics.
   */
  get currentWidget(): Widget | null {
    return this._currentWidget;
  }

  /**
   * Returns an iterator for the widgets inside the application shell.
   *
   * @param area - Optional regions in the shell whose widgets are iterated.
   */
  *widgets(area?: string): IterableIterator<Widget> {
    yield* (this.layout as BoxLayout).widgets;
  }

  /**
   * A message handler invoked on an `'update-request'` message.
   *
   * #### Notes
   * The default implementation of this handler is a no-op.
   */
  protected onUpdateRequest(msg: Message): void {
    super.onUpdateRequest(msg);
    this._updated.emit();
  }

  private _currentWidget: Widget | null;
  private _updated: Signal<MercuryShell, void>;
}

export class MercuryApp extends JupyterFrontEnd<JupyterFrontEnd.IShell> {
  /**
   * Construct a new application object.
   *
   * @param options The instantiation options for an application.
   */
  constructor(options: Partial<MercuryApp.IOptions> = {}) {
    super({ ...options, shell: options.shell ?? new MercuryShell() });
    if (options.mimeExtensions) {
      for (const plugin of createRendermimePlugins(options.mimeExtensions)) {
        this.registerPlugin(plugin);
      }
    }
  }

  /**
   * The name of the application.
   */
  readonly name = 'Mercury';

  /**
   * A namespace/prefix plugins may use to denote their provenance.
   */
  readonly namespace = this.name;

  /**
   * The version of the application.
   */
  readonly version = PageConfig.getOption('appVersion') ?? 'unknown';

  /**
   * The JupyterLab application paths dictionary.
   */
  get paths(): JupyterFrontEnd.IPaths {
    return {
      urls: {
        base: PageConfig.getOption('baseUrl'),
        notFound: PageConfig.getOption('notFoundUrl'),
        app: PageConfig.getOption('appUrl'),
        static: PageConfig.getOption('staticUrl'),
        settings: PageConfig.getOption('settingsUrl'),
        themes: PageConfig.getOption('themesUrl'),
        doc: PageConfig.getOption('docUrl'),
        translations: PageConfig.getOption('translationsApiUrl')
      },
      directories: {
        appSettings: PageConfig.getOption('appSettingsDir'),
        schemas: PageConfig.getOption('schemasDir'),
        static: PageConfig.getOption('staticDir'),
        templates: PageConfig.getOption('templatesDir'),
        themes: PageConfig.getOption('themesDir'),
        userSettings: PageConfig.getOption('userSettingsDir'),
        serverRoot: PageConfig.getOption('serverRoot'),
        workspaces: PageConfig.getOption('workspacesDir')
      }
    };
  }

  /**
   * Register plugins from a plugin module.
   *
   * @param mod - The plugin module to register.
   */
  registerPluginModule(mod: MercuryApp.IPluginModule): void {
    let data = mod.default;
    // Handle commonjs exports.
    if (!Object.prototype.hasOwnProperty.call(mod, '__esModule')) {
      data = mod as any;
    }
    if (!Array.isArray(data)) {
      data = [data];
    }
    data.forEach(item => {
      try {
        this.registerPlugin(item);
      } catch (error) {
        console.error(error);
      }
    });
  }

  /**
   * Register the plugins from multiple plugin modules.
   *
   * @param mods - The plugin modules to register.
   */
  registerPluginModules(mods: MercuryApp.IPluginModule[]): void {
    mods.forEach(mod => {
      this.registerPluginModule(mod);
    });
  }
}

export namespace MercuryApp {
  export interface IOptions
    extends JupyterFrontEnd.IOptions<JupyterFrontEnd.IShell>,
      Partial<IInfo> {}

  /**
   * The information about a RetroLab application.
   */
  export interface IInfo {
    /**
     * The mime renderer extensions.
     */
    readonly mimeExtensions: IRenderMime.IExtensionModule[];
  }

  /**
   * The interface for a module that exports a plugin or plugins as
   * the default value.
   */
  export interface IPluginModule {
    /**
     * The default export.
     */
    default: JupyterFrontEndPlugin<any> | JupyterFrontEndPlugin<any>[];
  }
}
