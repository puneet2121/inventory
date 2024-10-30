import React, { useRef, useState } from 'react';
import JsBarcode from 'jsbarcode';

const BarcodeGenerator = ({ barcodeValue }) => {
    const svgRef = useRef(null);
    const [inputValue, setInputValue] = useState(barcodeValue || "");

    // Generate Barcode on Value Change
    const generateBarcode = () => {
        JsBarcode(svgRef.current, inputValue, {
            format: "CODE128",
            width: 2,
            height: 40,
        });
    };

    return (
        <div>
            <h2>Generate Barcode</h2>
            <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Enter value for barcode"
            />
            <button onClick={generateBarcode}>Generate Barcode</button>
            <svg ref={svgRef}></svg>
        </div>
    );
};

export default BarcodeGenerator;
