import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ErrorState from "../../../shared/components/ErrorState";
import LoadingState from "../../../shared/components/LoadingState";
import SetupLayout from "../../../shared/components/SetupLayout";
import { ApiError } from "../../../shared/api/http";
import LogoutButton from "../../auth/components/LogoutButton";
import { saveSelection } from "../api/repositoriesApi";
import RepositoryChoices from "../components/RepositoryChoices";
import { useRepositoryList } from "../hooks/useRepositoryList";
import type { RepositoryItem } from "../types";

const SEARCH_DELAY_MS = 300;
// These errors have fixed, safe messages from the backend, so they can be shown as they are.
const SHOWABLE_ERRORS = new Set(["repository_not_found", "repository_unavailable", "not_connected"]);

function saveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 0) return "Could not reach DevPulse. Your choices are kept, so you can try again.";
    if (error.code !== null && SHOWABLE_ERRORS.has(error.code)) {
      return `${error.message} Your choices are kept; refresh the list and try again.`;
    }
  }
  return "Could not save your selection. Your choices are kept, so you can try again.";
}

export default function SelectRepositoriesPage() {
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  // Choices not saved yet, by repository ID. Kept while searching and paging.
  const [pending, setPending] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedCount, setSavedCount] = useState<number | null>(null);
  const { state, reload, refresh, gaveUp } = useRepositoryList(search, page);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(input.trim());
      setPage(1);
    }, SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [input]);

  function toggle(item: RepositoryItem) {
    setSavedCount(null);
    setPending((current) => {
      const next = !(current[item.id] ?? item.is_selected);
      const updated = { ...current };
      // Back to what is already saved: nothing to change for this repository.
      if (next === item.is_selected) delete updated[item.id];
      else updated[item.id] = next;
      return updated;
    });
  }

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    const entries = Object.entries(pending);
    try {
      const result = await saveSelection({
        select: entries.filter(([, wanted]) => wanted).map(([id]) => id),
        unselect: entries.filter(([, wanted]) => !wanted).map(([id]) => id),
      });
      setPending({});
      setSavedCount(result.selected_count);
      refresh();
    } catch (error) {
      setSaveError(saveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  const changeCount = Object.keys(pending).length;
  const added = Object.values(pending).filter(Boolean).length;
  const removed = changeCount - added;

  return (
    <SetupLayout
      crumb="Setup"
      action={
        <div className="setup-actions">
          <Link to="/dashboard" className="btn btn-ghost">
            Back to dashboard
          </Link>
          <LogoutButton className="btn btn-ghost" />
        </div>
      }
    >
      {state.status === "loading" && <LoadingState label="Loading your repositories…" />}
      {state.status === "error" && (
        <ErrorState
          title="Could not load your repositories"
          message="DevPulse could not load the list. Please try again."
          onRetry={reload}
        />
      )}
      {state.status === "not_connected" && (
        <div className="state">
          <p className="banner banner-warning">
            <span aria-hidden="true">!</span> Connect your GitHub account before choosing repositories.
          </p>
          <Link className="btn btn-primary" to="/connect">
            Connect GitHub <span aria-hidden="true">→</span>
          </Link>
        </div>
      )}
      {state.status === "ready" && (
        <div className="setup-grid">
          <section className="setup-intro">
            <h2>A clearer view of your engineering.</h2>
            <p>One secure connection. Your pull request activity, from the repositories you choose.</p>
            <ol className="steps" aria-label="Setup steps">
              <li className="step">
                <span aria-hidden="true">✓</span> Connect GitHub
              </li>
              <li className="step step-current" aria-current="step">
                <span>02</span> Select repositories
              </li>
            </ol>
            <p className="fine-print">
              READ-ONLY BY DEFAULT
              <br />
              Your source code stays on GitHub.
            </p>
          </section>

          <div className="setup-card">
            <p className="eyebrow">02 / Repositories</p>
            <h1 className="page-title">Choose your signal.</h1>
            <p className="setup-lead">
              Start with your active repositories. You can change this later.
            </p>

            {state.data.list_status === "syncing" ? (
              gaveUp ? (
                <div className="banner banner-warning" role="status">
                  <span aria-hidden="true">!</span> Fetching is taking longer than expected.
                  <button type="button" className="btn btn-secondary" onClick={reload}>
                    Check again
                  </button>
                </div>
              ) : (
                <p className="banner banner-info" role="status">
                  <span aria-hidden="true">↻</span> Fetching your repositories…
                </p>
              )
            ) : (
              <>
                <div className="field">
                  <label htmlFor="repo-search" className="visually-hidden">
                    Search repositories
                  </label>
                  <input
                    id="repo-search"
                    type="search"
                    className="input"
                    placeholder="Search repositories"
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                  />
                </div>

                {state.data.total === 0 && search === "" && (
                  <div className="setup-panel">
                    <strong>No repositories available yet.</strong>
                    <span>
                      Give the DevPulse GitHub App access to some repositories on GitHub, then check
                      again.
                    </span>
                    <button type="button" className="btn btn-secondary" onClick={reload}>
                      Check again
                    </button>
                  </div>
                )}
                {state.data.total === 0 && search !== "" && (
                  <p className="setup-lead">No repositories match “{search}”.</p>
                )}

                {state.data.total > 0 && (
                  <>
                    <p className="repo-summary">
                      <strong>{state.data.selected_count + added - removed} selected</strong> ·{" "}
                      {state.data.total} {search ? "matching" : "available"}
                    </p>
                    <RepositoryChoices
                      items={state.data.items}
                      pending={pending}
                      onToggle={toggle}
                      disabled={saving}
                    />
                    <Pager
                      page={state.data.page}
                      pageSize={state.data.page_size}
                      total={state.data.total}
                      onPage={setPage}
                    />
                  </>
                )}

                {saveError && (
                  <p className="banner banner-danger" role="alert">
                    <span aria-hidden="true">×</span> {saveError}
                  </p>
                )}
                {savedCount !== null && (
                  <p className="banner banner-success" role="status">
                    <span aria-hidden="true">✓</span> Your selection is saved. {savedCount}{" "}
                    {savedCount === 1 ? "repository is" : "repositories are"} selected.
                  </p>
                )}

                <div className="actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleSave}
                    disabled={saving || changeCount === 0}
                  >
                    {saving
                      ? "Saving…"
                      : changeCount === 0
                        ? "Save selection"
                        : `Save selection (${changeCount} ${changeCount === 1 ? "change" : "changes"})`}
                  </button>
                  <Link className="btn btn-secondary" to="/dashboard">
                    Back to dashboard
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </SetupLayout>
  );
}

type PagerProps = { page: number; pageSize: number; total: number; onPage: (page: number) => void };

function Pager({ page, pageSize, total, onPage }: PagerProps) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages === 1) return null;
  return (
    <nav className="pager" aria-label="Pages">
      <button type="button" className="btn btn-secondary" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        Previous
      </button>
      <span>
        Page {page} of {pages}
      </span>
      <button
        type="button"
        className="btn btn-secondary"
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
      >
        Next
      </button>
    </nav>
  );
}
