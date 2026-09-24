/** Lista de tableros de análisis guardados (RF-6.4), y su creación desde la
 * posición inicial, un FEN, un PGN pegado o el editor de posición (RF-6.1).
 *
 * Las cuatro formas terminan en el mismo sitio: el campo "FEN o PGN", que
 * `parseSource` convierte en la raíz y el árbol del tablero. El editor no es
 * una segunda forma de crear, es un ayudante que escribe en ese campo. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { Chess } from "chess.js";
import { useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { CustomPositionBadge } from "../../components/CustomPositionBadge";
import { FieldLabel } from "../../components/FieldLabel";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { buttonClasses, FIELD_CLASSES, PANEL_CLASSES } from "../../components/styles";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { STANDARD_STARTING_FEN } from "./position";
import { PositionEditor } from "./PositionEditor";
import { createRoot, fromPgn, type TreeNode } from "./tree";

export function BoardsPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isEditorOpen, setEditorOpen] = useState(false);

  const boardsQuery = useQuery({ queryKey: ["boards"], queryFn: api.listBoards });

  const createMutation = useMutation({
    mutationFn: (body: { title: string; root_fen: string; tree_json: TreeNode }) =>
      api.createBoard(body),
    onSuccess: (board) => {
      queryClient.invalidateQueries({ queryKey: ["boards"] });
      navigate({ to: "/boards/$boardId", params: { boardId: String(board.id) } });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteBoard,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["boards"] }),
  });

  /** Qué tablero se está borrando ahora mismo: la mutación es una sola para
   * toda la lista, así que sin mirar sus `variables` se marcarían todas las
   * filas a la vez. */
  function isDeleting(boardId: number): boolean {
    return deleteMutation.isPending && deleteMutation.variables === boardId;
  }

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const parsed = parseSource(source);
    if (!parsed) {
      setError("No se reconoce eso como FEN ni como PGN. Déjalo vacío para empezar de cero.");
      return;
    }
    createMutation.mutate({
      title: title.trim() || "Tablero sin título",
      root_fen: parsed.rootFen,
      tree_json: parsed.tree,
    });
  }

  return (
    <div className="space-y-6">
      {/* Título y frase de entrada van juntos, como en Motores: sueltos,
          había que anular el `space-y-6` de la pantalla con un margen
          negativo para que la frase no pareciera de otra sección. */}
      <div>
        <h1 className="text-2xl font-bold">Tableros de análisis</h1>
        <p className="mt-1 text-sm opacity-70">
          Para partidas presenciales, posiciones de libro o ideas sueltas. No cuentan en tus
          estadísticas.
        </p>
      </div>

      <form
        onSubmit={handleCreate}
        className={`space-y-3 p-4 ${PANEL_CLASSES}`}
      >
        <div className="flex flex-wrap gap-3">
          <FieldLabel label="Título">
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Mi partida del club"
              className={`w-64 ${FIELD_CLASSES}`}
            />
          </FieldLabel>
        </div>

        <FieldLabel
          label="FEN o PGN de partida"
          hint="Opcional: vacío empieza en la posición estándar."
        >
          <textarea
            value={source}
            onChange={(event) => setSource(event.target.value)}
            rows={3}
            placeholder="rnbqkbnr/pppppppp/... o 1. e4 e5 2. Nf3"
            className={`w-full font-mono text-xs ${FIELD_CLASSES}`}
          />
        </FieldLabel>

        {/* La cuarta forma de partir (RF-6.1), para quien no tiene un FEN a
            mano: monta la posición sobre un tablero y escribe su FEN en el
            campo de arriba. Va debajo del campo y no en otra pantalla porque
            es un ayudante de ese campo, no otra manera de crear. */}
        <div>
          <Button onClick={() => setEditorOpen(!isEditorOpen)}>
            {isEditorOpen ? "Cancelar" : "Editor de posición"}
          </Button>
          {/* Qué hace el botón, a la vista y no en un `title`, que con teclado
              no aparece nunca: es la misma línea con la que el visor explica
              sus acciones y la que cerró la fila 103 (criterios C-6 y C-7). */}
          {!isEditorOpen && (
            <p className="mt-1 text-xs opacity-60">
              Coloca las piezas sobre un tablero y escribe esa posición en el campo de arriba.
            </p>
          )}
        </div>
        {isEditorOpen && (
          <PositionEditor
            initialFen={source.trim() || STANDARD_STARTING_FEN}
            onUse={(fen) => {
              setSource(fen);
              setEditorOpen(false);
              setError(null);
            }}
          />
        )}

        {/* El error de validación usa el mismo recuadro que el de la API:
            antes uno era un párrafo rojo suelto y el otro un `ErrorBox`, a dos
            líneas de distancia dentro del mismo formulario. */}
        {error && <ErrorBox error={new Error(error)} />}
        {createMutation.isError && <ErrorBox error={createMutation.error} />}

        <Button type="submit" variant="primary" disabled={createMutation.isPending}>
          {createMutation.isPending ? "Creando…" : "Crear tablero"}
        </Button>
      </form>

      {deleteMutation.isError && <ErrorBox error={deleteMutation.error} />}
      {boardsQuery.isPending && <Spinner label="Cargando tus tableros…" />}
      {boardsQuery.isError && <ErrorBox error={boardsQuery.error} onRetry={boardsQuery.refetch} />}

      {boardsQuery.data?.length === 0 && (
        <EmptyState title="Todavía no has guardado ningún tablero" />
      )}

      {boardsQuery.data && boardsQuery.data.length > 0 && (
        <ul className="space-y-2">
          {boardsQuery.data.map((board) => (
            <li
              key={board.id}
              className={`flex items-center justify-between gap-3 px-3 py-2 ${PANEL_CLASSES}`}
            >
              <div className="flex-1">
                <span className="font-medium">{board.title}</span>
                {board.is_own_game && (
                  <span className="ml-2">
                    <Badge
                      tone="info"
                      title="Está publicado como una partida más: cuenta en Partidas y en tus Estadísticas"
                    >
                      partida propia
                    </Badge>
                  </span>
                )}
                {/* Un tablero se crea desde un FEN casi siempre: decir de qué
                    posición arranca es más útil aquí que en ningún otro sitio. */}
                {board.root_fen !== STANDARD_STARTING_FEN && (
                  <span className="ml-2">
                    <CustomPositionBadge />
                  </span>
                )}
                <span className="ml-2 text-xs opacity-60">
                  actualizado {formatDate(board.updated_at)}
                </span>
              </div>
              {/* Abrir un elemento se hace igual que en Partidas: un enlace con
                  aspecto de botón al final de la fila, separado de eliminar. */}
              <Link
                to="/boards/$boardId"
                params={{ boardId: String(board.id) }}
                className={buttonClasses("secondary", "sm")}
              >
                Ver tablero
              </Link>
              {/* Destruir siempre pregunta, aquí y en el árbol de variantes:
                  no hay deshacer para ninguna de las dos. Y mientras la
                  petición viaja lo dice, como el resto de escrituras de la
                  aplicación (criterio C-3): la fila se quedaba igual y daba la
                  sensación de que el botón no había hecho nada. */}
              <Button
                variant="danger"
                size="sm"
                disabled={isDeleting(board.id)}
                onClick={() => {
                  if (window.confirm(`¿Eliminar el tablero "${board.title}"? No se puede deshacer.`)) {
                    deleteMutation.mutate(board.id);
                  }
                }}
              >
                {isDeleting(board.id) ? "Eliminando…" : "Eliminar"}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

interface ParsedSource {
  rootFen: string;
  tree: TreeNode;
}

/** Acepta un FEN, un PGN o nada (RF-6.1). Se intenta primero como FEN porque
 * es más específico: un PGN nunca se confunde con un FEN válido.
 *
 * El PGN pasa por el mismo `fromPgn` que el panel "Importar PGN" del tablero
 * (RF-6.7), no por `loadPgn` de chess.js: aquel conserva las variantes y los
 * comentarios y este los descarta, y pegar el mismo archivo al crear o
 * después no puede dar dos tableros distintos (criterio C-5 de
 * docs/07-coherencia-ui.md). */
function parseSource(source: string): ParsedSource | null {
  const trimmedSource = source.trim();
  if (!trimmedSource) {
    return { rootFen: STANDARD_STARTING_FEN, tree: createRoot(STANDARD_STARTING_FEN) };
  }

  try {
    const chess = new Chess(trimmedSource);
    return { rootFen: chess.fen(), tree: createRoot(chess.fen()) };
  } catch {
    // no era un FEN; se intenta como PGN
  }

  try {
    const parsed = fromPgn(trimmedSource);
    return { rootFen: parsed.root.fen, tree: parsed.root };
  } catch {
    return null; // tampoco es un PGN con jugadas legales
  }
}
