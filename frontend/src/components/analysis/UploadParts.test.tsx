import { describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RemoveBadge } from './UploadParts';

describe('RemoveBadge', () => {
  it('removes the file without also opening the picker behind it', async () => {
    const onRemove = vi.fn();
    const onTileClick = vi.fn();
    render(
      <div onClick={onTileClick}>
        <RemoveBadge title="Remove image" onRemove={onRemove} />
      </div>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Remove image' }));

    expect(onRemove).toHaveBeenCalledOnce();
    expect(onTileClick).not.toHaveBeenCalled();
  });

  it('is styled by a rule that exists, since index.css lacks its old Tailwind classes', () => {
    render(<RemoveBadge title="Remove image" onRemove={() => {}} />);
    expect(screen.getByRole('button', { name: 'Remove image' })).toHaveClass('remove-badge');
    const css = readFileSync('src/styles/ui-components.css', 'utf8');
    expect(css).toMatch(/\.remove-badge \{[^}]*position: absolute;[^}]*background: #ef4444;/);
  });
});
