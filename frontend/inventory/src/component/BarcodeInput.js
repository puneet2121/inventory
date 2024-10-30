import React, { useState } from 'react';
import axios from 'axios';

const BarcodeInput = () => {
    const [barcode, setBarcode] = useState("");

    const handleAddBarcode = async () => {
        try {
            await axios.post('http://127.0.0.1:8000/api/add-barcode/', { code: barcode });
            alert("Barcode added successfully!");
            setBarcode("");
        } catch (error) {
            console.error("Error adding barcode:", error);
            alert("Failed to add barcode");
        }
    };

    return (
        <div>
            <h2>Add Barcode</h2>
            <input
                type="text"
                placeholder="Enter or scan barcode"
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
            />
            <button onClick={handleAddBarcode}>Add Barcode</button>
        </div>
    );
};

export default BarcodeInput;
