import { describe, expect, it, vi } from 'vitest';
import { createEvent, fireEvent, render, screen } from '@testing-library/react';
import { useDropZone } from './useDropZone';

// jsdom has no DragEvent, so build the leave event as a MouseEvent to carry relatedTarget.
function dragLeave(target: Element, relatedTarget: Element) {
  fireEvent(target, new MouseEvent('dragleave', { bubbles: true, cancelable: true, relatedTarget }));
}

function Zone({ onFile }: { onFile: (file: File) => void }) {
  const { isDragging, handlers } = useDropZone(onFile);
  return (
    <div data-testid="zone" {...handlers}>
      <span data-testid="child">{isDragging ? 'dragging' : 'idle'}</span>
    </div>
  );
}

describe('useDropZone', () => {
  it('marks the zone as dragging on drag enter and hands the dropped file over', () => {
    const onFile = vi.fn();
    render(<Zone onFile={onFile} />);
    const zone = screen.getByTestId('zone');
    const file = new File(['x'], 'verse.png', { type: 'image/png' });

    fireEvent.dragEnter(zone);
    expect(screen.getByTestId('child')).toHaveTextContent('dragging');

    fireEvent.drop(zone, { dataTransfer: { files: [file] } });
    expect(screen.getByTestId('child')).toHaveTextContent('idle');
    expect(onFile).toHaveBeenCalledWith(file);
  });

  it('stays in the dragging state while the pointer moves onto a child', () => {
    render(<Zone onFile={vi.fn()} />);
    const zone = screen.getByTestId('zone');
    fireEvent.dragEnter(zone);
    dragLeave(zone, screen.getByTestId('child'));
    expect(screen.getByTestId('child')).toHaveTextContent('dragging');
  });

  it('clears the dragging state when the pointer leaves the zone', () => {
    render(<Zone onFile={vi.fn()} />);
    const zone = screen.getByTestId('zone');
    fireEvent.dragEnter(zone);
    dragLeave(zone, document.body);
    expect(screen.getByTestId('child')).toHaveTextContent('idle');
  });

  it('ignores a drop without files', () => {
    const onFile = vi.fn();
    render(<Zone onFile={onFile} />);
    fireEvent.drop(screen.getByTestId('zone'), { dataTransfer: { files: [] } });
    expect(onFile).not.toHaveBeenCalled();
  });

  it('prevents the browser default so the file is not opened in the tab', () => {
    render(<Zone onFile={vi.fn()} />);
    const zone = screen.getByTestId('zone');
    const dragOver = createEvent.dragOver(zone);
    fireEvent(zone, dragOver);
    expect(dragOver.defaultPrevented).toBe(true);
  });
});
