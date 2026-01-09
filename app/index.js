// Inspired by: https://github.com/jupyterlab/jupyterlab/blob/master/dev_mode/index.js

import { PageConfig, URLExt } from '@jupyterlab/coreutils';

// Patch FAST color scale sort to avoid recursion issues in some builds.
import './fast-colors-sort-patch';
// Patch @jupyter/ydoc to avoid premature access before Yjs types attach.
import './ydoc-attach-patch';

import './style';
import './extraStyle';

// mercury application
import mercuryPlugins, { MercuryApp } from 'mercury-application';

// mime extensions
import jsMime from '@jupyterlab/javascript-extension';
import jsonMime from '@jupyterlab/json-extension';
import pdfMime from '@jupyterlab/pdf-extension';
import vegaMime from '@jupyterlab/vega5-extension';

// core extensions (import plugin arrays)
import applicationExt from '@jupyterlab/application-extension';
import apputilsExt from '@jupyterlab/apputils-extension';
import codemirrorExt from '@jupyterlab/codemirror-extension';
import docmanagerExt from '@jupyterlab/docmanager-extension';
import mathjaxExt from '@jupyterlab/mathjax-extension';
import markedparserExt from '@jupyterlab/markedparser-extension';
import notebookExt from '@jupyterlab/notebook-extension';
import rendermimeExt from '@jupyterlab/rendermime-extension';
import shortcutsExt from '@jupyterlab/shortcuts-extension';
import translationExt from '@jupyterlab/translation-extension';

// Trick to include package required by ipywidgets in the webpack shared scope.
import('@jupyterlab/console').catch(reason => {
  console.error('Failed to import @jupyterlab/console', reason);
});

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
  // eslint-disable-next-line no-undef
  await __webpack_init_sharing__('default');
  const container = window._JUPYTERLAB[scope];
  // eslint-disable-next-line no-undef
  await container.init(__webpack_share_scopes__.default);
}

async function createModule(scope, module) {
  const factory = await window._JUPYTERLAB[scope].get(module);
  return factory();
}

function normalizePlugins(extensionModule) {
  // Handle commonjs or es2015 modules
  let exports;
  if (Object.prototype.hasOwnProperty.call(extensionModule, '__esModule')) {
    exports = extensionModule.default;
  } else {
    exports = extensionModule;
  }
  return Array.isArray(exports) ? exports : [exports];
}

function filterPlugins(plugins, allowIds) {
  const allow = new Set(allowIds);
  return plugins.filter(p => allow.has(p.id));
}

async function main() {
  const disabled = [];
  const mods = [];

  function* activePlugins(extension) {
    const plugins = normalizePlugins(extension);
    for (let plugin of plugins) {
      if (PageConfig.Extension.isDisabled(plugin.id)) {
        disabled.push(plugin.id);
        continue;
      }
      yield plugin;
    }
  }

  // mime extensions list (no Promise.all)
  const mimeExtensions = [
    ...normalizePlugins(jsMime),
    ...normalizePlugins(jsonMime),
    ...normalizePlugins(pdfMime),
    ...normalizePlugins(vegaMime)
  ];

  // base mods (no dynamic import())
  const baseMods = [
    // mercury plugins
    mercuryPlugins,

    // @jupyterlab plugins (filtered)
    filterPlugins(normalizePlugins(applicationExt), [
      //'@jupyterlab/application-extension:commands',
      //'@jupyterlab/application-extension:context-menu'
    ]),

    filterPlugins(normalizePlugins(apputilsExt), [
      // '@jupyterlab/apputils-extension:palette',
      //'@jupyter/apputils-extension:sanitizer',
      '@jupyterlab/apputils-extension:sanitizer',
      '@jupyterlab/apputils-extension:settings',
      //'@jupyterlab/apputils-extension:sessionDialogs',
      '@jupyterlab/apputils-extension:toolbar-registry'
    ]),

    filterPlugins(normalizePlugins(codemirrorExt), [
      '@jupyterlab/codemirror-extension:services',
      '@jupyterlab/codemirror-extension:binding',
      '@jupyterlab/codemirror-extension:codemirror',
      '@jupyterlab/codemirror-extension:languages',
      '@jupyterlab/codemirror-extension:extensions',
      '@jupyterlab/codemirror-extension:themes'
    ]),

    filterPlugins(normalizePlugins(docmanagerExt), [
      '@jupyterlab/docmanager-extension:plugin',
      '@jupyterlab/docmanager-extension:manager',
      '@jupyterlab/docmanager-extension:opener'
    ]),

    mathjaxExt,
    markedparserExt,

    filterPlugins(normalizePlugins(notebookExt), [
      '@jupyterlab/notebook-extension:factory',
      '@jupyterlab/notebook-extension:tracker',
      '@jupyterlab/notebook-extension:widget-factory'
    ]),

    rendermimeExt,
    shortcutsExt,

    filterPlugins(normalizePlugins(translationExt), [
      '@jupyterlab/translation-extension:translator'
    ])
  ];

  // ---- Federated extensions still supported (Module Federation kept) ----
  const extensionRaw = PageConfig.getOption('federated_extensions');
  const extension_data = extensionRaw ? JSON.parse(extensionRaw) : [];

  // Add the base frontend extensions
  baseMods.forEach(p => {
    for (let plugin of activePlugins(p)) {
      mods.push(plugin);
    }
  });

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

  const federatedExtensions = await Promise.allSettled(federatedExtensionPromises);
  federatedExtensions.forEach(p => {
    if (p.status === 'fulfilled') {
      for (let plugin of activePlugins(p.value)) {
        mods.push(plugin);
      }
    } else {
      console.error(p.reason);
    }
  });

  const federatedMimeExtensions = await Promise.allSettled(federatedMimeExtensionPromises);
  federatedMimeExtensions.forEach(p => {
    if (p.status === 'fulfilled') {
      for (let plugin of activePlugins(p.value)) {
        mimeExtensions.push(plugin);
      }
    } else {
      console.error(p.reason);
    }
  });

  (await Promise.allSettled(federatedStylePromises))
    .filter(({ status }) => status === 'rejected')
    .forEach(({ reason }) => console.error(reason));

  const app = new MercuryApp({ mimeExtensions });
  app.registerPluginModules(mods);
  await app.start();
}

window.addEventListener('load', main); 
