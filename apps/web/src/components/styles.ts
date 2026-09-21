/** Recetas de clases compartidas por la interfaz.
 *
 * Viven en un módulo sin componentes por dos razones: Vite solo puede hacer
 * fast-refresh de un archivo que exporta únicamente componentes (lo avisa
 * eslint), y así hay un único sitio donde mirar cuando algo se ve distinto de
 * lo que debería (criterio C-2 de docs/07-coherencia-ui.md).
 *
 * Los componentes `Button` y `Panel` son la vía normal; estas constantes y
 * funciones son para lo que no puede ser un `button` ni un `div`: un `<form>`,
 * un `<li>`, o un `<Link>` del router que se ve como un botón pero debe seguir
 * siendo un enlace.
 */

export type ButtonVariant = "primary" | "secondary" | "danger";
export type ButtonSize = "md" | "sm";

const BUTTON_BASE_CLASSES =
  "rounded transition-colors disabled:cursor-not-allowed disabled:opacity-50";

const BUTTON_VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-slate-900 text-white hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-300",
  secondary:
    "border border-slate-300 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800",
  danger:
    "border border-slate-300 text-red-700 hover:bg-red-50 dark:border-slate-700 dark:text-red-300 dark:hover:bg-red-950",
};

const BUTTON_SIZE_CLASSES: Record<ButtonSize, string> = {
  md: "px-3 py-1.5 text-sm",
  sm: "px-2 py-1 text-xs",
};

export function buttonClasses(
  variant: ButtonVariant = "secondary",
  size: ButtonSize = "md",
): string {
  return `${BUTTON_BASE_CLASSES} ${BUTTON_VARIANT_CLASSES[variant]} ${BUTTON_SIZE_CLASSES[size]}`;
}

/** Caja con borde: la unidad de agrupación visual. Para un `div` normal usa el
 * componente `Panel`; esto es para un `<form>` o un `<li>`. */
export const PANEL_CLASSES =
  "rounded border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900";

/** Campos de formulario (input, select, textarea). Estaban escritos a mano en
 * nueve sitios y con dos fondos oscuros distintos, así que dos filtros
 * equivalentes se veían distintos según la pantalla. */
export const FIELD_CLASSES =
  "rounded border border-slate-300 bg-white px-2 py-1.5 dark:border-slate-700 dark:bg-slate-950";

/** Alto máximo de las listas navegables (jugadas, variantes) y ancho del panel
 * lateral de las dos pantallas de tablero. Eran cuatro valores distintos para
 * el mismo layout: 22rem y 24rem de panel, 28rem y 26rem de lista. */
export const MOVE_LIST_HEIGHT_CLASS = "max-h-[26rem]";
export const BOARD_SIDEBAR_GRID_CLASS = "grid gap-4 lg:grid-cols-[minmax(0,1fr)_24rem]";

/** La frase de ayuda bajo el tablero, donde se anuncian los atajos: misma
 * forma y mismo sitio en las dos pantallas que tienen tablero (criterio C-1:
 * el teclado se anuncia, no se descubre probando). */
export const BOARD_HINT_CLASSES = "text-center text-xs opacity-60";

/** El enlace de navegación que no está marcado. El activo se ve como el botón
 * primario (`buttonClasses("primary")`), así que este lleva su mismo relleno y
 * su mismo tamaño de texto para que marcar uno no mueva a los demás. Lo usan
 * la barra de navegación principal y la sub-navegación de Entrenamiento, que
 * lo tenían copiado carácter a carácter (criterio C-2). */
export const NAV_LINK_CLASSES =
  "rounded px-3 py-1.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800";

/** Fila y celda de una tabla de datos (`components/DataTable.tsx`), que las
 * escribe quien pinta cada fila y por eso no puede recibirlas del componente. */
export const TABLE_ROW_CLASSES =
  "border-t border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900";
export const TABLE_CELL_CLASSES = "px-3 py-2";
