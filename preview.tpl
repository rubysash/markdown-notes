/* Browser Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Base Styles */
html, body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #212529;
    color: #aaa;
    font-size: 16px;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
}

body {
    padding: 2rem;
    max-width: 100%;
    margin: 0;
    background-color: #212529;
}

/* Typography Hierarchy */
h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    line-height: 1.25;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    color: #ffffff;
}

h1 {
    font-size: 2.5rem;
    border-bottom: 2px solid #495057;
    padding-bottom: 0.75rem;
    margin-top: 0;
    color: #f8f9fa;
}

h2 {
    font-size: 2rem;
    color: #ff6b6b;
    border-bottom: 1px solid #495057;
    padding-bottom: 0.5rem;
}

h3 {
    font-size: 1.5rem;
    color: #007bff;
}

h4 {
    font-size: 1.25rem;
    color: #eee;
}

h5, h6 {
    font-size: 1rem;
    color: #eee;
}

/* Paragraphs and Text */
p {
    margin-bottom: 1rem;
    margin-top: 0;
    color: #ffffff;
}

/* Emphasis */
strong, b {
    font-weight: 700;
    color: #ffd700;
}

em, i {
    font-style: italic;
    color: #ffffff;
}

/* Code Blocks */
code {
    background-color: #343a40;
    color: #fd7e14;
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
    font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.875em;
    border: 1px solid #495057;
}

pre {
    background-color: #1e2125;
    border: 1px solid #495057;
    border-radius: 0.5rem;
    padding: 1.25rem;
    overflow-x: auto;
    margin: 1.5rem 0;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.3);
}

pre code {
    background: none;
    color: #e9ecef;
    padding: 0;
    border: none;
    font-size: 0.9rem;
}

/* Blockquotes */
blockquote {
    border-left: 4px solid #007bff;
    margin: 1.5rem 0;
    padding: 1rem 1.5rem;
    background-color: #343a40;
    border-radius: 0 0.375rem 0.375rem 0;
    color: #ced4da;
    font-style: italic;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.2);
}

blockquote p:last-child {
    margin-bottom: 0;
}

/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1.5rem 0;
    background-color: #343a40;
    border-radius: 0.5rem;
    overflow: hidden;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.2);
}

th {
    background-color: #495057;
    color: #f8f9fa;
    font-weight: 600;
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 2px solid #6c757d;
}

td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #495057;
    color: #dee2e6;
}

tr:nth-child(even) {
    background-color: #2c3034;
}

tr:hover {
    background-color: #3d4348;
}

/* Lists */
ul, ol {
    margin: 1rem 0;
    padding-left: 2rem;
    color: #dee2e6;
}

li {
    margin-bottom: 0.5rem;
    line-height: 1.6;
}

li::marker {
    color: #6c757d;
}

/* Nested lists */
li ul, li ol {
    margin: 0.5rem 0;
}

/* Links */
a {
    color: #007bff;
    text-decoration: none;
    transition: color 0.15s ease-in-out;
}

a:hover {
    color: #0056b3;
    text-decoration: underline;
}

a:visited {
    color: #6f42c1;
}

/* Horizontal Rules */
hr {
    border: none;
    height: 1px;
    background-color: #495057;
    margin: 2rem 0;
}

/* Images */
img {
    max-width: 100%;
    height: auto;
    border-radius: 0.375rem;
    box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.3);
}

/* Task Lists */
input[type="checkbox"] {
    margin-right: 0.5rem;
    accent-color: #007bff;
}

/* Keyboard Keys */
kbd {
    background-color: #495057;
    border: 1px solid #6c757d;
    border-radius: 0.25rem;
    box-shadow: inset 0 -1px 0 #6c757d;
    color: #f8f9fa;
    font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.875em;
    padding: 0.125rem 0.375rem;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background-color: #343a40;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background-color: #6c757d;
    border-radius: 4px;
    border: 1px solid #495057;
}

::-webkit-scrollbar-thumb:hover {
    background-color: #adb5bd;
}

/* Print Styles */
@media print {
    body {
        background-color: white !important;
        color: black !important;
    }
    
    a {
        color: #0000EE !important;
    }
}