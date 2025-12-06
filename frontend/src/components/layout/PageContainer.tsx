import type { PropsWithChildren } from 'react';

interface PageContainerProps {
  className?: string;
}

export function PageContainer({ children, className }: PropsWithChildren<PageContainerProps>) {
  const classes = [
    'w-full',
    'max-w-6xl',
    'mx-auto',
    'px-6',
    className || '',
  ].join(' ').trim();

  return <div className={classes}>{children}</div>;
}
