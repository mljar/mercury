export interface ISelectWidget {
  label: string | null;
  value: string | null;
  input: string;
  choices: string[];
  multi: boolean | undefined;
}

export interface ICheckboxWidget {
  label: string | null;
  value: boolean | null;
  input: string;
}

export interface INumericWidget {
  label: string | null;
  value: number | null;
  input: string;
  min: number;
  max: number;
  step: number;
}

export interface ISliderWidget {
  vertical: boolean | null;
  label: string | null;
  value: number | null;
  input: string;
  min: number | null;
  max: number | null;
  step: number | null;
}

export interface IRangeWidget {
  vertical: boolean | null;
  label: string | null;
  value: [number, number] | null;
  input: string;
  min: number | null;
  max: number | null;
  step: number | null;
}

export interface IFileWidget {
  label: string | null;
  value: string | null;
  input: string;
  maxFileSize: string | null;
}

export interface ITextWidget {
  label: string | null;
  value: string | undefined;
  input: string;
  rows: number | null;
}

export interface IOutputFilesWidget {
  output: string;
  input: null;
  value: null;
}

export interface IMarkdownWidget {
  output: string;
  input: null;  // we need to add input to be IWidget
  value: string;
}

export interface IButtonWidget {
  label: string | null;
  style: string;
  input: string;
  value: string | boolean | null;
}


export type IWidget =
  | ISelectWidget
  | ICheckboxWidget
  | INumericWidget
  | ISliderWidget
  | IRangeWidget
  | IFileWidget
  | ITextWidget
  | IOutputFilesWidget
  | IMarkdownWidget
  | IButtonWidget;

export function isSelectWidget(widget: IWidget): widget is ISelectWidget {
  return (widget as ISelectWidget).input === "select";
}

export function isCheckboxWidget(widget: IWidget): widget is ICheckboxWidget {
  return (widget as ICheckboxWidget).input === "checkbox";
}

export function isNumericWidget(widget: IWidget): widget is INumericWidget {
  return (widget as INumericWidget).input === "numeric";
}

export function isSliderWidget(widget: IWidget): widget is ISliderWidget {
  return (widget as ISliderWidget).input === "slider";
}

export function isRangeWidget(widget: IWidget): widget is IRangeWidget {
  return (widget as IRangeWidget).input === "range";
}

export function isFileWidget(widget: IWidget): widget is IFileWidget {
  return (widget as IFileWidget).input === "file";
}

export function isTextWidget(widget: IWidget): widget is ITextWidget {
  return (widget as ITextWidget).input === "text";
}

export function isOutputFilesWidget(widget: IWidget): widget is IOutputFilesWidget {
  return (widget as IOutputFilesWidget).output === "dir";
}

export function isMarkdownWidget(widget: IWidget): widget is IMarkdownWidget {
  return (widget as IMarkdownWidget).output === "markdown";
}

export function isButtonWidget(widget: IWidget): widget is IButtonWidget {
  return (widget as IButtonWidget).input === "button";
}
