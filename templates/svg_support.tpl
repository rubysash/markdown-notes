/* SVG Support Styles for QWebEngineView */
svg, .markdown-svg {
    display: block !important;
    margin: 1rem auto !important;
    max-width: 100% !important;
    height: auto !important;
    border-radius: 0.375rem;
    background-color: transparent;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.3);
    /* Ensure proper rendering in QWebEngineView */
    image-rendering: auto !important;
    shape-rendering: auto !important;
}

/* Ensure SVG maintains aspect ratio in web view */
svg[width][height] {
    width: auto !important;
    max-width: 100% !important;
    height: auto !important;
}

/* Container for SVG elements */
.svg-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 1rem 0;
    padding: 1rem;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
    border: 1px solid #495057;
}

.svg-container svg {
    margin: 0;
    box-shadow: none;
}

/* Force SVG to render properly in QWebEngine */
svg * {
    max-width: none !important;
    vector-effect: non-scaling-stroke;
}

/* Handle inline SVG elements */
p svg, li svg {
    display: inline-block !important;
    vertical-align: middle !important;
    margin: 0 0.25rem !important;
    max-height: 1.5em !important;
    width: auto !important;
}

/* Base64 image support */
img[src^="data:"] {
    max-width: 100% !important;
    height: auto !important;
    border-radius: 0.375rem;
    box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.3);
    margin: 1rem auto !important;
    display: block !important;
}

/* QWebEngineView specific fixes */
@media screen {
    svg {
        /* Ensure crisp rendering */
        image-rendering: -webkit-optimize-contrast !important;
        image-rendering: -moz-crisp-edges !important;
        image-rendering: pixelated !important;
        image-rendering: crisp-edges !important;
    }
}

/* Dark theme adjustments for SVG */
@media (prefers-color-scheme: dark) {
    svg {
        filter: brightness(0.95) contrast(1.05);
    }
}

/* Responsive SVG behavior */
@media (max-width: 768px) {
    svg {
        max-width: 100% !important;
        height: auto !important;
    }
}

/* Scrollbar styling for SVG containers */
.svg-container::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

.svg-container::-webkit-scrollbar-track {
    background-color: #343a40;
    border-radius: 4px;
}

.svg-container::-webkit-scrollbar-thumb {
    background-color: #6c757d;
    border-radius: 4px;
    border: 1px solid #495057;
}

.svg-container::-webkit-scrollbar-thumb:hover {
    background-color: #adb5bd;
}