/** La cabecera de las pantallas de entrenamiento (RF-4): el título de la
 * sección, lo que hace la pantalla concreta y la navegación entre las formas
 * de entrenar.
 *
 * Está en un solo sitio porque las tres pantallas —los puzzles (RF-4.1), la
 * antesala del sparring y una partida de sparring (RF-4.3)— son la misma
 * sección y tienen que encabezarse igual (criterio C-2 de
 * docs/07-coherencia-ui.md); lo único que cambia es la frase, que llega como
 * `children`.
 *
 * "Entrenamiento" tiene varias pantallas —y le faltan el drill de aperturas
 * (RF-4.2) y el plan semanal (RF-4.5)—, así que la elección vive dentro de la
 * sección y no en la navegación principal, que si no crecería una entrada por
 * cada forma de entrenar. Los enlaces se ven como el enlace activo de la
 * navegación principal y salen de la misma receta (`buttonClasses`), para que
 * "dónde estoy" se lea igual en los dos sitios.
 */
import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { buttonClasses, NAV_LINK_CLASSES } from "../../components/styles";

/** `exact` distingue la pestaña que es también la raíz de la sección: sin él,
 * "/training" —que es prefijo de todas— se quedaría marcada en todas. Sparring
 * no lo lleva porque tiene una pantalla debajo, la de una partida concreta. */
const TRAINING_TABS = [
  { to: "/training", label: "Puzzles", exact: true },
  { to: "/training/sparring", label: "Sparring", exact: false },
] as const;

export function TrainingHeader({ children }: { children: ReactNode }) {
  return (
    <>
      <div>
        <h1 className="text-2xl font-bold">Entrenamiento</h1>
        <p className="mt-1 text-sm opacity-70">{children}</p>
      </div>

      <nav className="flex gap-1" aria-label="Formas de entrenar">
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
