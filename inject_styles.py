import re
import os

css_content = """/* Global Poster Styles (Desktop & Mobile Base) */
.nv-hero-slider {
    margin: 20px auto !important;
    max-width: 1400px !important;
    position: relative !important;
}

.nv-hero-track {
    position: relative !important;
    border-radius: 20px !important;
    overflow: hidden !important;
    min-height: 480px !important;
    display: flex !important;
    background: #0a0b10 !important;
}

.nv-hero-slide {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    transition: opacity 0.5s ease !important;
    display: flex !important;
    align-items: center !important;
}

.nv-hero-slide.is-active {
    opacity: 1 !important;
    position: relative !important;
}

.nv-hero-bg {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
    z-index: 1 !important;
}

.nv-hero-overlay {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    background: linear-gradient(to right, #0a0b10 10%, rgba(10, 11, 16, 0.7) 50%, transparent 100%), linear-gradient(to top, #0a0b10 0%, transparent 30%) !important;
    z-index: 2 !important;
}

.nv-hero-content {
    position: relative !important;
    z-index: 3 !important;
    padding: 50px !important;
    max-width: 800px !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 16px !important;
    align-items: flex-start !important;
}

.nv-featured-badge {
    border: 1px solid #7c3aed !important;
    background: rgba(124, 58, 237, 0.15) !important;
    color: #c4b5fd !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    padding: 6px 14px !important;
    border-radius: 20px !important;
    letter-spacing: 0.5px !important;
}
.nv-featured-badge i { display: none !important; }

.nv-hero-title {
    font-size: 42px !important;
    font-weight: 800 !important;
    line-height: 1.1 !important;
    color: #ffffff !important;
    margin: 0 !important;
}

.nv-hero-tags {
    display: flex !important;
    gap: 10px !important;
    flex-wrap: wrap !important;
    margin-top: -5px !important;
}
.nv-hero-tags span {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #f3f4f6 !important;
    padding: 6px 14px !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
}

.nv-hero-desc {
    color: #d1d5db !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    margin: 0 !important;
    display: -webkit-box !important;
    -webkit-line-clamp: 2 !important;
    -webkit-box-orient: vertical !important;
    overflow: hidden !important;
}

.nv-hero-meta {
    display: grid !important;
    grid-template-columns: auto auto !important;
    gap: 10px 40px !important;
    color: #d1d5db !important;
    font-size: 14px !important;
    margin-top: 5px !important;
}
.nv-hero-meta div a {
    color: #d1d5db !important;
    text-decoration: none !important;
}
.nv-hero-meta strong {
    color: #a78bfa !important;
    font-weight: 700 !important;
    margin-right: 4px !important;
}

.nv-hero-actions {
    display: flex !important;
    gap: 15px !important;
    margin-top: 15px !important;
}

.nv-hero-actions .nv-btn {
    padding: 12px 28px !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    text-decoration: none !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: transform 0.2s, background 0.2s !important;
    border: none !important;
}
.nv-hero-actions .nv-btn i { display: none !important; }

.nv-hero-actions .nv-btn-primary {
    background: #8b5cf6 !important;
    color: #ffffff !important;
}
.nv-hero-actions .nv-btn-primary:hover {
    background: #7c3aed !important;
    transform: translateY(-2px) !important;
}

.nv-hero-actions .nv-btn-secondary {
    background: transparent !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
}
.nv-hero-actions .nv-btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    transform: translateY(-2px) !important;
}

/* Dots Navigation */
.nv-hero-dots {
    position: absolute !important;
    bottom: 25px !important;
    right: 25px !important;
    display: flex !important;
    gap: 8px !important;
    z-index: 10 !important;
}
.nv-hero-dots button {
    width: 8px !important;
    height: 8px !important;
    border-radius: 50% !important;
    background: #4b5563 !important;
    border: none !important;
    padding: 0 !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
}
.nv-hero-dots button.is-active {
    background: #8b5cf6 !important;
    width: 24px !important;
    border-radius: 4px !important;
}

/* Mobile Adjustments for Poster & Overall Layout */
@media (max-width: 768px) {
    .nv-hero-track {
        min-height: 380px !important;
    }
    .nv-hero-content {
        padding: 20px !important;
    }
    .nv-hero-title {
        font-size: 28px !important;
    }
    .nv-hero-actions {
        flex-direction: column !important;
        width: 100% !important;
    }
    .nv-hero-actions .nv-btn {
        width: 100% !important;
    }
    .nv-hero-meta {
        grid-template-columns: 1fr !important;
        gap: 5px !important;
    }
    .nv-hero-dots {
        bottom: 10px !important;
        right: 10px !important;
    }

    /* Header layout */
    .nv-header {
        position: sticky;
        top: 0;
        z-index: 1000;
        background: #1c1e22 !important;
        border-bottom: none !important;
    }
    .nv-header-inner {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 10px 15px !important;
        height: auto !important;
    }
    
    /* Logo */
    .nv-logo {
        margin-right: auto !important;
        display: flex !important;
        align-items: center !important;
    }
    .nv-logo img {
        height: 28px !important; 
        width: auto !important;
    }

    /* Hide elements that shouldn't be in the top bar */
    .nv-mobile-toggle,
    .nv-theme-toggle,
    .nv-title-lang-toggle,
    .nv-search {
        display: none !important;
    }

    /* Auth actions (Sign In / Sign Up) */
    .nv-auth-actions {
        display: flex !important;
        gap: 10px !important;
        align-items: center !important;
        margin-left: auto !important;
    }
    
    .nv-login-btn, .nv-signup-btn {
        padding: 8px 16px !important;
        font-size: 14px !important;
        border-radius: 8px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        line-height: 1 !important;
        height: auto !important;
    }
    
    .nv-login-btn {
        background: transparent !important;
        border: 1px solid #4f5359 !important;
        color: #fff !important;
    }
    
    .nv-signup-btn {
        background: #14ff00 !important;
        color: #000 !important;
        font-weight: 700 !important;
        border: none !important;
    }
    .nv-signup-btn i {
        display: none !important;
    }

    /* Bottom Navigation */
    .nv-nav {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        top: auto !important;
        background: #1c1e22 !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-around !important;
        padding: 10px 5px 25px 5px !important;
        z-index: 9999 !important;
        border-top: 1px solid #2d3035 !important;
        transform: none !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 100% !important;
        height: auto !important;
        clip-path: none !important;
        overflow: visible !important;
        transition: none !important;
    }
    
    .nv-nav a {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 12px !important;
        color: #99a4b0 !important;
        gap: 6px !important;
        text-decoration: none !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        width: auto !important;
        flex: 1 !important;
    }
    
    .nv-nav a i {
        font-size: 20px !important;
        margin: 0 !important;
    }

    .nv-nav a.active {
        color: #fff !important;
    }

    /* Adjust main content body to prevent overlap with bottom nav */
    body {
        padding-bottom: 80px !important;
        background-color: #0f1114 !important;
        color: #fff !important;
    }
    
    /* Watchlist & Genre tabs adjustments */
    .an-watchlist-section {
        padding: 0 15px !important;
        margin-top: 15px !important;
    }
    .an-watchlist-card {
        background: #1c1e22 !important;
        border-radius: 12px !important;
    }
    .nv-genre-tabs {
        padding: 0 15px !important;
        margin: 15px 0 !important;
    }
    .nv-genre-tabs button {
        background: #2d3035 !important;
        color: #99a4b0 !important;
        border: none !important;
        border-radius: 8px !important;
    }
    .nv-genre-tabs button.active {
        background: #4f5359 !important;
        color: #fff !important;
    }

    /* Featured Anime Cards like game thumbnails */
    .nv-featured-section, .nv-updates-section, .nv-ongoing-section {
        padding: 0 15px !important;
    }
    .nv-featured-grid, .nv-updates-grid, .nv-ongoing-grid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 10px !important;
    }
    .nv-anime-card {
        background: transparent !important;
        border-radius: 8px !important;
    }
    .nv-anime-thumb {
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    .nv-anime-title {
        font-size: 12px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        margin-top: 5px !important;
    }
    .nv-anime-genres {
        display: none !important;
    }
    .nv-section-title-wrap h2, .nv-section-title {
        font-size: 18px !important;
    }

    /* Watch page specific adjustments */
    .nv-watch-layout {
        display: flex !important;
        flex-direction: column !important;
    }
    .nv-player-section {
        padding: 0 !important;
    }
    .nv-watch-sidebar {
        padding: 15px !important;
        margin-top: 0 !important;
    }
    
    /* Video Player adjustments */
    .nv-video-wrapper, .nv-player-container {
        border-radius: 0 !important;
    }
    .nv-video-wrapper iframe {
        height: 250px !important;
    }
}"""

style_block = f"<style>\\n{css_content}\\n</style>"

files = ['anineko.html', 'anineko_ep1.html', 'anineko_watch.html', 'frontend/index.html']

for file_path in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the previous style block injected
        new_content = re.sub(r'<style>.*?Custom Mobile Overrides.*?</style>', style_block, content, flags=re.DOTALL)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"Updated {file_path}")
    except Exception as e:
        print(f"Failed to update {file_path}: {e}")
