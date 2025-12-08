/**
 * SearchBar Component
 * Search posts and users in the community
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, Loader2, User, FileText } from 'lucide-react';
import { searchPosts, searchUsers } from '../../services/community';
import type { Post, CommunityUser } from '../../types/community';

interface SearchResult {
  type: 'post' | 'user';
  data: Post | CommunityUser;
}

export function SearchBar() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const [postsRes, usersRes] = await Promise.all([
          searchPosts(query, { limit: 5 }),
          searchUsers(query, 5),
        ]);

        const combined: SearchResult[] = [];
        
        // Add users first
        if (usersRes.success && usersRes.users) {
          usersRes.users.forEach(user => {
            combined.push({ type: 'user', data: user });
          });
        }
        
        // Add posts
        if (postsRes.success && postsRes.posts) {
          postsRes.posts.forEach(post => {
            combined.push({ type: 'post', data: post });
          });
        }

        setResults(combined);
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  const handleResultClick = (result: SearchResult) => {
    setIsOpen(false);
    setQuery('');
    
    if (result.type === 'user') {
      const user = result.data as CommunityUser;
      navigate(`/community/user/${user.id}`);
    } else {
      const post = result.data as Post;
      navigate(`/community/post/${post.id}`);
    }
  };

  const handleClear = () => {
    setQuery('');
    setResults([]);
    inputRef.current?.focus();
  };

  const truncateText = (text: string, maxLength: number = 60): string => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  return (
    <div className="search-bar-container" ref={containerRef}>
      <div className="search-input-wrapper">
        <Search className="search-icon" size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
        <input
          ref={inputRef}
          type="text"
          placeholder="Search posts or users..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          style={{ paddingLeft: '44px', paddingRight: '40px' }}
        />
        {query && (
          <button className="search-clear-btn" onClick={handleClear} type="button">
            <X size={16} />
          </button>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && query.trim() && (
        <div className="search-results-dropdown">
          {loading && results.length === 0 ? (
            <div className="search-no-results">
              <Loader2 className="animate-spin" size={20} />
              <span style={{ marginLeft: '8px' }}>Searching...</span>
            </div>
          ) : results.length === 0 ? (
            <div className="search-no-results">
              No results found for "{query}"
            </div>
          ) : (
            <>
              {results.map((result, index) => (
                <button
                  key={`${result.type}-${result.type === 'user' ? (result.data as CommunityUser).id : (result.data as Post).id}-${index}`}
                  className="search-result-item"
                  onClick={() => handleResultClick(result)}
                  type="button"
                >
                  {result.type === 'user' ? (
                    <>
                      <div className="search-result-avatar">
                        <User size={16} />
                      </div>
                      <div className="search-result-info">
                        <span className="search-result-name">
                          {(result.data as CommunityUser).username}
                        </span>
                        <span className="search-result-preview">User</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="search-result-avatar">
                        <FileText size={16} />
                      </div>
                      <div className="search-result-info">
                        <span className="search-result-name">
                          {truncateText((result.data as Post).content)}
                        </span>
                        <span className="search-result-preview">
                          by {(result.data as Post).users?.username || 'Unknown'}
                        </span>
                      </div>
                    </>
                  )}
                </button>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
