// Inspired by: https://github.com/jupyterlab/jupyterlab/blob/master/dev_mode/index.js

import { PageConfig, URLExt } from '@jupyterlab/coreutils';

import './style';
import './extraStyle';

function loadScript(url) {
  return new Promise((resolve, reject) => {
    const newScript = document.createElement('script');
    newScript.onerror = reject;
    newScript.onload = resolve;
    newScript.async = true;
    document.head.appendChild(newScript);
    newScript.src = url;
  });
}
async function loadComponent(url, scope) {
  await loadScript(url);

  // From MIT-licensed https://github.com/module-federation/module-federation-examples/blob/af043acd6be1718ee195b2511adf6011fba4233c/advanced-api/dynamic-remotes/app1/src/App.js#L6-L12
  // eslint-disable-next-line no-undef
  await __webpack_init_sharing__('default');
  const container = window._JUPYTERLAB[scope];
  // Initialize the container, it may provide shared modules and may need ours
  // eslint-disable-next-line no-undef
  await container.init(__webpack_share_scopes__.default);
}

async function createModule(scope, module) {
  try {
    const factory = await window._JUPYTERLAB[scope].get(module);
    return factory();
  } catch (e) {
    console.warn(
      `Failed to create module: package: ${scope}; module: ${module}`
    );
    throw e;
  }
}

/**
 * The main function
 */
async function main() {
  const mercury = await import('mercury-application');

  const mimeExtensionsMods = [
    import('@jupyterlab/javascript-extension'),
    import('@jupyterlab/json-extension'),
    import('@jupyterlab/pdf-extension'),
    import('@jupyterlab/vega5-extension')
  ];
  const mimeExtensions = await Promise.all(mimeExtensionsMods);

  const disabled = [];
  // TODO: formalize the way the set of initial extensions and plugins are specified
  let baseMods = [
    // mercury plugins
    mercury.default,

    // @jupyterlab plugins
    import('@jupyterlab/application-extension').then(mod =>
      mod.default.filter(({ id }) =>
        [
          '@jupyterlab/application-extension:commands',
          '@jupyterlab/application-extension:context-menu'
        ].includes(id)
      )
    ),
    import('@jupyterlab/apputils-extension').then(mod =>
      mod.default.filter(({ id }) =>
        [
          '@jupyterlab/apputils-extension:palette',
          '@jupyter/apputils-extension:sanitizer',
          '@jupyterlab/apputils-extension:sanitizer',
          '@jupyterlab/apputils-extension:settings',
          '@jupyterlab/apputils-extension:sessionDialogs',
          // Theming removed - light theme CSS directly imported in packages/application/style/base.css
          // '@jupyterlab/apputils-extension:themes',
          '@jupyterlab/apputils-extension:toolbar-registry'
        ].includes(id)
      )
    ),
    import('@jupyterlab/codemirror-extension').then(mod =>
      mod.default.filter(({ id }) =>
        [
          '@jupyterlab/codemirror-extension:services',
          '@jupyterlab/codemirror-extension:binding',
          '@jupyterlab/codemirror-extension:codemirror',
          '@jupyterlab/codemirror-extension:languages',
          '@jupyterlab/codemirror-extension:extensions',
          '@jupyterlab/codemirror-extension:themes'
        ].includes(id)
      )
    ),
    import('@jupyterlab/docmanager-extension').then(mod =>
      mod.default.filter(({ id }) =>
        [
          '@jupyterlab/docmanager-extension:plugin',
          '@jupyterlab/docmanager-extension:manager',
          '@jupyterlab/docmanager-extension:opener'
        ].includes(id)
      )
    ),
    import('@jupyterlab/mathjax-extension'),
    import('@jupyterlab/markedparser-extension'),
    import('@jupyterlab/notebook-extension').then(mod =>
      mod.default.filter(({ id }) =>
        [
          '@jupyterlab/notebook-extension:factory',
          '@jupyterlab/notebook-extension:tracker',
          '@jupyterlab/notebook-extension:widget-factory'
        ].includes(id)
      )
    ),
    import('@jupyterlab/rendermime-extension'),
    import('@jupyterlab/shortcuts-extension'),
    // import('@jupyterlab/theme-light-extension'),
    import('@jupyterlab/translation-extension').then(mod =>
      mod.default.filter(({ id }) =>
        ['@jupyterlab/translation:translator'].includes(id)
      )
    )
  ];

  // Trick to include package required by ipywidgets in the webpack shared scope.
  import('@jupyterlab/console').catch(reason => {
    console.error('Failed to import @jupyterlab/console', reason);
  });

  /**
   * Iterate over active plugins in an extension.
   *
   * #### Notes
   * This also populates the disabled
   */
  function* activePlugins(extension) {
    // Handle commonjs or es2015 modules
    let exports;
    if (Object.prototype.hasOwnProperty.call(extension, '__esModule')) {
      exports = extension.default;
    } else {
      // CommonJS exports.
      exports = extension;
    }

    let plugins = Array.isArray(exports) ? exports : [exports];
    for (let plugin of plugins) {
      if (PageConfig.Extension.isDisabled(plugin.id)) {
        disabled.push(plugin.id);
        continue;
      }
      yield plugin;
    }
  }

  const extension_data = JSON.parse(
    PageConfig.getOption('federated_extensions')
  );

  const mods = [];
  const federatedExtensionPromises = [];
  const federatedMimeExtensionPromises = [];
  const federatedStylePromises = [];

  const extensions = await Promise.allSettled(
    extension_data.map(async data => {
      await loadComponent(
        `${URLExt.join(
          PageConfig.getOption('fullLabextensionsUrl'),
          data.name,
          data.load
        )}`,
        data.name
      );
      return data;
    })
  );

  extensions.forEach(p => {
    if (p.status === 'rejected') {
      // There was an error loading the component
      console.error(p.reason);
      return;
    }

    const data = p.value;
    if (data.extension) {
      federatedExtensionPromises.push(createModule(data.name, data.extension));
    }
    if (data.mimeExtension) {
      federatedMimeExtensionPromises.push(
        createModule(data.name, data.mimeExtension)
      );
    }
    if (data.style) {
      federatedStylePromises.push(createModule(data.name, data.style));
    }
  });

  // Add the base frontend extensions
  const baseFrontendMods = await Promise.all(baseMods);
  baseFrontendMods.forEach(p => {
    for (let plugin of activePlugins(p)) {
      mods.push(plugin);
    }
  });

  // Add the federated extensions.
  const federatedExtensions = await Promise.allSettled(
    federatedExtensionPromises
  );
  federatedExtensions.forEach(p => {
    if (p.status === 'fulfilled') {
      for (let plugin of activePlugins(p.value)) {
        mods.push(plugin);
      }
    } else {
      console.error(p.reason);
    }
  });

  // Add the federated mime extensions.
  const federatedMimeExtensions = await Promise.allSettled(
    federatedMimeExtensionPromises
  );
  federatedMimeExtensions.forEach(p => {
    if (p.status === 'fulfilled') {
      for (let plugin of activePlugins(p.value)) {
        mimeExtensions.push(plugin);
      }
    } else {
      console.error(p.reason);
    }
  });

  // Load all federated component styles and log errors for any that do not
  (await Promise.allSettled(federatedStylePromises))
    .filter(({ status }) => status === 'rejected')
    .forEach(({ reason }) => {
      console.error(reason);
    });

  const MercuryApp = mercury.MercuryApp;
  const app = new MercuryApp({ mimeExtensions });

  app.registerPluginModules(mods);

  await app.start();
}

window.addEventListener('load', main);
