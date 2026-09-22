/** La cabecera de las pantallas de entrenamiento (RF-4): el título de la
 * sección, lo que hace la pantalla concreta y la navegación entre las formas
 * de entrenar.
 *
 * Está en un solo sitio porque todas las pantallas de la sección —el plan
 * semanal (RF-4.5), los puzzles (RF-4.1), el drill de aperturas (RF-4.2), los
 * errores que re-jugar (RF-4.4), la antesala del sparring y una partida de
 * sparring (RF-4.3)— tienen que encabezarse igual (criterio C-2 de
 * docs/07-coherencia-ui.md); lo único que cambia es la frase, que llega como
 * `children`.
 *
 * "Entrenamiento" tiene seis pantallas, así que la elección vive dentro de la
 * sección y no en la navegación principal, que si no crecería una entrada por
 * cada forma de entrenar. Los enlaces se ven como el enlace activo de la
 * navegación principal y salen de la misma receta (`buttonClasses`), para que
 * "dónde estoy" se lea igual en los dos sitios.
 */
import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { buttonClasses, NAV_LINK_CLASSES } from "../../components/styles";

/** El plan va primero porque es la portada de la sección: es la pantalla que
 * dice por dónde empezar, y las otras cuatro son adónde te manda.
 *
 * `exact` distingue la pestaña que es también la raíz de la sección: sin él,
 * "/training" —que es prefijo de todas— se quedaría marcada en todas. Sparring
 * no lo lleva porque tiene una pantalla debajo, la de una partida concreta. */
const TRAINING_TABS = [
  { to: "/training", label: "Plan", exact: true },
  { to: "/training/puzzles", label: "Puzzles", exact: false },
  { to: "/training/drills", label: "Aperturas", exact: false },
  { to: "/training/replays", label: "Re-jugar", exact: false },
  { to: "/training/sparring", label: "Sparring", exact: false },
] as const;

export function TrainingHeader({ children }: { children: ReactNode }) {
  return (
    <>
      <div>
        <h1 className="text-2xl font-bold">Entrenamiento</h1>
        <p className="mt-1 text-sm opacity-70">{children}</p>
      </div>

      {/* `flex-wrap` porque con la quinta pestaña (RF-4.5) la fila ya no cabe
          en una ventana estrecha: es lo mismo que le pasó a la fila de
          acciones del visor con su cuarto control (criterio C-2). */}
      <nav className="flex flex-wrap gap-1" aria-label="Formas de entrenar">
        {TRAINING_TABS.map((tab) => (
          <Link
            key={tab.to}
            to={tab.to}
            activeOptions={{ exact: tab.exact }}
            className={NAV_LINK_CLASSES}
            activeProps={{ className: buttonClasses("primary") }}
          >
            {tab.label}
          </Link>
        ))}
      </nav>
    </>
  );
}
