// ABOUTME: Monaco-based Python code editor with syntax highlighting and autocomplete
// ABOUTME: Provides IDE-like experience for editing transformation scripts

import React, { useRef, useEffect } from 'react';
import Editor, { Monaco } from '@monaco-editor/react';
import { editor } from 'monaco-editor';

interface PythonEditorProps {
    value: string;
    onChange: (value: string) => void;
    height?: string;
    readOnly?: boolean;
    minimap?: boolean;
    lineNumbers?: boolean;
    theme?: 'vs-dark' | 'light';
    placeholder?: string;
}

const PythonEditor: React.FC<PythonEditorProps> = ({
    value,
    onChange,
    height = '400px',
    readOnly = false,
    minimap = false,
    lineNumbers = true,
    theme = 'vs-dark',
    placeholder = '# Enter your Python code here...'
}) => {
    const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
    const monacoRef = useRef<Monaco | null>(null);

    const handleEditorWillMount = (monaco: Monaco) => {
        // Configure Python language settings
        monaco.languages.registerCompletionItemProvider('python', {
            provideCompletionItems: (model, position) => {
                const word = model.getWordUntilPosition(position);
                const range = {
                    startLineNumber: position.lineNumber,
                    endLineNumber: position.lineNumber,
                    startColumn: word.startColumn,
                    endColumn: word.endColumn
                };
                
                // Add custom completions for safe modules
                const suggestions = [
                    // Pandas suggestions
                    {
                        label: 'pd.DataFrame',
                        kind: monaco.languages.CompletionItemKind.Class,
                        insertText: 'pd.DataFrame(${1:data})',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        documentation: 'Create a new DataFrame'
                    },
                    {
                        label: 'pd.read_parquet',
                        kind: monaco.languages.CompletionItemKind.Function,
                        insertText: 'pd.read_parquet("${1:file_path}")',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        documentation: 'Read a parquet file'
                    },
                    {
                        label: 'df.groupby',
                        kind: monaco.languages.CompletionItemKind.Method,
                        insertText: 'groupby("${1:column}").${2:agg}(${3})',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        documentation: 'Group DataFrame by column(s)'
                    },
                    // NumPy suggestions
                    {
                        label: 'np.array',
                        kind: monaco.languages.CompletionItemKind.Function,
                        insertText: 'np.array(${1:data})',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        documentation: 'Create a NumPy array'
                    },
                    {
                        label: 'np.mean',
                        kind: monaco.languages.CompletionItemKind.Function,
                        insertText: 'np.mean(${1:array})',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        documentation: 'Calculate mean of array'
                    },
                    // Input/Output helpers
                    {
                        label: 'input_data',
                        kind: monaco.languages.CompletionItemKind.Variable,
                        insertText: 'input_data',
                        documentation: 'Input DataFrame provided by the pipeline'
                    },
                    {
                        label: 'output_data',
                        kind: monaco.languages.CompletionItemKind.Variable,
                        insertText: 'output_data = ${1:result}',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        documentation: 'Set the output data for the pipeline'
                    }
                ].map(item => ({ ...item, range }));

                return { suggestions };
            }
        });

        // Set Python language configuration
        monaco.languages.setLanguageConfiguration('python', {
            comments: {
                lineComment: '#',
            },
            brackets: [
                ['[', ']'],
                ['(', ')'],
                ['{', '}'],
            ],
            autoClosingPairs: [
                { open: '[', close: ']' },
                { open: '(', close: ')' },
                { open: '{', close: '}' },
                { open: '"', close: '"' },
                { open: "'", close: "'" },
            ],
            surroundingPairs: [
                { open: '[', close: ']' },
                { open: '(', close: ')' },
                { open: '{', close: '}' },
                { open: '"', close: '"' },
                { open: "'", close: "'" },
            ],
            indentationRules: {
                increaseIndentPattern: /^.*:\s*$/,
                decreaseIndentPattern: /^\s*(elif|else|except|finally).*:/,
            },
        });
    };

    const handleEditorDidMount = (editor: editor.IStandaloneCodeEditor, monaco: Monaco) => {
        editorRef.current = editor;
        monacoRef.current = monaco;

        // Set initial placeholder if empty
        if (!value) {
            const model = editor.getModel();
            if (model) {
                model.setValue(placeholder);
            }
        }

        // Configure editor options
        editor.updateOptions({
            minimap: { enabled: minimap },
            lineNumbers: lineNumbers ? 'on' : 'off',
            readOnly,
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            formatOnPaste: true,
            formatOnType: true,
            automaticLayout: true,
            suggest: {
                insertMode: 'replace',
                snippetsPreventQuickSuggestions: false,
            }
        });

        // Add keyboard shortcuts
        editor.addAction({
            id: 'format-python',
            label: 'Format Python Code',
            keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyF],
            run: (ed) => {
                ed.getAction('editor.action.formatDocument')?.run();
            }
        });
    };

    const handleChange = (value: string | undefined) => {
        onChange(value || '');
    };

    return (
        <div className="border rounded-md overflow-hidden">
            <Editor
                height={height}
                defaultLanguage="python"
                theme={theme}
                value={value}
                onChange={handleChange}
                beforeMount={handleEditorWillMount}
                onMount={handleEditorDidMount}
                options={{
                    minimap: { enabled: minimap },
                    lineNumbers: lineNumbers ? 'on' : 'off',
                    readOnly,
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    formatOnPaste: true,
                    formatOnType: true,
                    automaticLayout: true,
                    tabSize: 4,
                    insertSpaces: true,
                    folding: true,
                    foldingStrategy: 'indentation',
                    showFoldingControls: 'mouseover',
                    renderWhitespace: 'selection',
                    quickSuggestions: {
                        other: true,
                        comments: false,
                        strings: true
                    },
                    parameterHints: {
                        enabled: true
                    },
                    suggestOnTriggerCharacters: true,
                    acceptSuggestionOnCommitCharacter: true,
                    snippetSuggestions: 'inline',
                    fontSize: 14,
                    fontFamily: "'Fira Code', 'Cascadia Code', Consolas, monospace",
                    fontLigatures: true,
                }}
            />
        </div>
    );
};

export default PythonEditor;

// Example usage component
export const PythonEditorExample: React.FC = () => {
    const [code, setCode] = React.useState(`# Example transformation script
import pandas as pd
import numpy as np

# Read input data
df = input_data

# Perform transformations
df['new_column'] = df['value'] * 2
df_grouped = df.groupby('category').agg({
    'value': ['mean', 'std'],
    'count': 'sum'
})

# Set output
output_data = df_grouped
`);

    return (
        <div className="p-4">
            <h3 className="text-lg font-semibold mb-2">Python Script Editor</h3>
            <PythonEditor
                value={code}
                onChange={setCode}
                height="500px"
            />
        </div>
    );
};