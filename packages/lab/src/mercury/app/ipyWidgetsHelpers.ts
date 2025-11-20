import { CodeCell } from '@jupyterlab/cells';
import type { IRenderMimeRegistry } from '@jupyterlab/rendermime';

/**
 * MIME type used by ipywidgets renderers in Jupyter.
 */
const WIDGET_MIMETYPE = 'application/vnd.jupyter.widget-view+json';

/** Collect widget model_ids from a CodeCell’s OutputArea model. */
export function getWidgetModelIdsFromCell(cell: CodeCell): string[] {
  const ids: string[] = [];
  const oaModel = cell.outputArea.model;

  for (let i = 0; i < oaModel.length; i++) {
    const output = oaModel.get(i);
    const data = output.data as any;
    if (data && WIDGET_MIMETYPE in data) {
      const payload = data[WIDGET_MIMETYPE];
      const modelId =
        typeof payload === 'string'
          ? (() => {
              try {
                return JSON.parse(payload).model_id;
              } catch {
                return undefined;
              }
            })()
          : payload?.model_id;
      if (modelId) {
        ids.push(modelId);
      }
    }
  }
  return ids;
}

/** Resolve an ipywidgets model safely, returns undefined if not found. */
export async function resolveIpyModel(
  manager: any,
  id: string
): Promise<any | undefined> {
  if (!manager) {
    return undefined;
  }

  if (typeof manager.getModel === 'function') {
    try {
      return manager.getModel(id);
    } catch {
      return undefined;
    }
  }

  if (typeof manager.get_model === 'function') {
    try {
      const res = manager.get_model(id);
      if (res && typeof res.then === 'function') {
        return await res.catch(() => undefined);
      }
      return res;
    } catch {
      return undefined;
    }
  }

  const map = (manager as any)?._models;
  if (map && typeof map.get === 'function') {
    try {
      const res = map.get(id);
      if (res && typeof res.then === 'function') {
        return await res.catch(() => undefined);
      }
      return res;
    } catch {
      return undefined;
    }
  }

  return undefined;
}

/** Get the ipywidgets WidgetManager instance from a rendermime registry. */
export async function getWidgetManager(
  rendermime: IRenderMimeRegistry
): Promise<any | null> {
  const factory: any = rendermime.getFactory(WIDGET_MIMETYPE);
  if (!factory) {
    return null;
  }

  const unwrap = async (x: any) =>
    x?.promise ? await x.promise : typeof x?.then === 'function' ? await x : x;

  if (factory.widgetManager) {
    return await unwrap(factory.widgetManager);
  }

  const rmAny: any = rendermime as any;
  if (rmAny.widgets?.manager) {
    return await unwrap(rmAny.widgets.manager);
  }

  if (typeof factory.createRenderer === 'function') {
    const r: any = factory.createRenderer({ mimeType: WIDGET_MIMETYPE });
    const cand =
      r?.manager ?? r?._manager ?? r?.widgets?.manager ?? factory?._manager;
    return await unwrap(cand);
  }

  return await unwrap((factory as any)._manager ?? null);
}
