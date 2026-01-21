import { useState } from 'react';
import './InputPanel.css';

const InputPanel = ({ onBuildGraph, onUploadPDF, onClearGraph, loading }) => {
    const [text, setText] = useState('');
    const [file, setFile] = useState(null);

    const handleTextSubmit = (e) => {
        e.preventDefault();
        if (text.trim()) {
            onBuildGraph(text);
        }
    };

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile && selectedFile.type === 'application/pdf') {
            setFile(selectedFile);
        } else {
            alert('Please select a valid PDF file');
        }
    };

    const handleFileUpload = () => {
        if (file) {
            onUploadPDF(file);
            setFile(null);
        }
    };

    const handleClear = () => {
        setText('');
        setFile(null);
        onClearGraph();
    };

    return (
        <div className="input-panel">
            <h2>Input Document</h2>

            <form onSubmit={handleTextSubmit} className="text-input-form">
                <label htmlFor="text-input">Enter Text:</label>
                <textarea
                    id="text-input"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Enter your text here to extract entities and relationships..."
                    rows={6}
                    disabled={loading}
                />
                <button type="submit" disabled={loading || !text.trim()}>
                    {loading ? 'Processing...' : 'Build Graph from Text'}
                </button>
            </form>

            <div className="divider">OR</div>

            <div className="file-input-section">
                <label htmlFor="file-input">Upload PDF:</label>
                <input
                    id="file-input"
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    disabled={loading}
                />
                {file && <p className="file-name">Selected: {file.name}</p>}
                <button
                    onClick={handleFileUpload}
                    disabled={loading || !file}
                >
                    {loading ? 'Processing...' : 'Build Graph from PDF'}
                </button>
            </div>

            <button
                onClick={handleClear}
                className="clear-button"
                disabled={loading}
            >
                Clear Graph
            </button>
        </div>
    );
};

export default InputPanel;
