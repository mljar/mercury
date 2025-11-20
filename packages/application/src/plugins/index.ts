/* eslint-disable no-inner-declarations */
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { MercuryApp } from '../app';
import { plugin } from './mercury';

/**
 * The default paths for Mercury app.
 */
const paths: JupyterFrontEndPlugin<JupyterFrontEnd.IPaths> = {
  id: 'mercury-application:paths',
  autoStart: true,
  provides: JupyterFrontEnd.IPaths,
  activate: (app: JupyterFrontEnd): JupyterFrontEnd.IPaths => {
    if (!(app instanceof MercuryApp)) {
      throw new Error(`${paths.id} can only be activated in Mercury.`);
    }
    return app.paths;
  }
};

export default [paths, plugin];
