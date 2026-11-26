import type { RepositoryItem } from "../types";

type Props = {
  items: RepositoryItem[];
  // Choices the user has made but not saved yet, by repository ID.
  pending: Record<string, boolean>;
  onToggle: (item: RepositoryItem) => void;
  disabled: boolean;
};

export default function RepositoryChoices({ items, pending, onToggle, disabled }: Props) {
  return (
    <ul className="repo-list" aria-label="Repositories">
      {items.map((item) => {
        const checked = pending[item.id] ?? item.is_selected;
        return (
          <li key={item.id}>
            <label className={`repo-row${checked ? " repo-row-selected" : ""}`}>
              <input
                type="checkbox"
                checked={checked}
                disabled={disabled}
                onChange={() => onToggle(item)}
              />
              <span className="repo-name">{item.full_name}</span>
              {item.is_private && <span className="badge badge-neutral">Private</span>}
            </label>
          </li>
        );
      })}
    </ul>
  );
}
