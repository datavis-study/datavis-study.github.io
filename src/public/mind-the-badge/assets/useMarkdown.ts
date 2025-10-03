import { useState, useEffect } from 'react';

const useMarkdown = (path?: string) => {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!path || typeof path !== 'string') {
      setContent('');
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetch(path)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load markdown');
        return res.text();
      })
      .then(setContent)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [path]);

  return { content, loading, error };
};

export default useMarkdown; 