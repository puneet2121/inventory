import React, { useState, useRef } from 'react';
import { BrowserMultiFormatReader } from '@zxing/library';

const BarcodeScanner = ({ onDetected }) => {
    const [scanning, setScanning] = useState(false);
    const videoRef = useRef(null);

    const startScanner = () => {
        setScanning(true);
        const codeReader = new BrowserMultiFormatReader();
        codeReader.decodeOnceFromVideoDevice(undefined, videoRef.current)
            .then(result => {
                setScanning(false);
                onDetected(result.text);
            })
            .catch(err => console.error("Error scanning barcode:", err));
    };

    return (
        <div>
            <h2>Scan Barcode</h2>
            {scanning ? (
                <video ref={videoRef} style={{ width: '100%' }} />
            ) : (
                <button onClick={startScanner}>Start Scanning</button>
            )}
        </div>
    );
};

export default BarcodeScanner;
