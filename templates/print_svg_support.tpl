/* Print SVG Support Styles */
svg {
    max-width: 100% !important;
    display: block !important;
    margin: 12pt auto !important;
    page-break-inside: avoid !important;
    border: 0.5pt solid #cccccc !important;
    background-color: white !important;
    box-sizing: border-box !important;
}

/* This rule ensures all elements inside the SVG scale correctly. */
svg * {
    max-width: none !important;
    vector-effect: non-scaling-stroke;
}

/* Specific sizing for SVG elements */
svg[width][height] {
    /* Preserve aspect ratio while constraining size */
    width: auto !important;
    max-width: 100% !important;
    max-height: 400pt !important;
}

/* SVG container for print */
.svg-container {
    display: block !important;
    margin: 12pt auto !important;
    padding: 6pt !important;
    page-break-inside: avoid !important;
    background-color: white !important;
    border: 0.5pt solid #cccccc !important;
    text-align: center !important;
    max-width: 100% !important;
}

.svg-container svg {
    margin: 0 !important;
    border: none !important;
}

/* Base64 images in print */
img[src^="data:"] {
    max-width: 100% !important;
    height: auto !important;
    margin: 6pt auto !important;
    display: block !important;
    page-break-inside: avoid !important;
    border: 0.5pt solid #cccccc !important;
    max-height: 400pt !important;
}

/* Regular images in print */
img {
    max-width: 100% !important;
    height: auto !important;
    margin: 6pt auto !important;
    display: block !important;
    page-break-inside: avoid !important;
    border: 0.5pt solid #cccccc !important;
    max-height: 400pt !important;
}

/* Inline SVG adjustments for print */
p svg, li svg {
    display: inline-block !important;
    vertical-align: middle !important;
    margin: 0 3pt !important;
    max-height: 18pt !important;
    width: auto !important;
    border: none !important;
}

/* Force proper scaling for print */
@media print {
    svg {
        filter: none !important;
        background-color: white !important;
        color: black !important;
        print-color-adjust: exact !important;
        -webkit-print-color-adjust: exact !important;
    }
    
    img {
        filter: none !important;
        print-color-adjust: exact !important;
        -webkit-print-color-adjust: exact !important;
    }
    
    /* Ensure page breaks work properly */
    svg, img {
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }
}

/* Responsive constraints for different page sizes */
@page {
    margin: 0.5in;
}

/* Additional constraints for very large SVGs */
svg[width="200"], svg[height="200"] {
    width: 144pt !important;
    height: 144pt !important;
}