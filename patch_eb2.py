import os

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

# Removing the class from the top of the file
eb_code = """
class TabelaErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false, error: null, info: null }; }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  componentDidCatch(error, info) { this.setState({ info }); console.error("TABELA CRASHED", error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 bg-red-900 border-2 border-red-500 rounded text-white overflow-auto max-w-full">
           <h2 className="text-xl font-bold mb-4">CRASH DETECTADO NA TABELA MAPA!</h2>
           <p className="font-mono text-sm mb-2 text-yellow-300">{this.state.error?.toString()}</p>
           <pre className="text-xs text-red-200 mt-2 p-2 bg-red-950 rounded">{this.state.info?.componentStack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}
"""

if eb_code in code:
    code = code.replace(eb_code, "")

# Finding the end of the imports
# Just replace the last import with the import + eb_code
code = code.replace(
    "import { createPortal } from 'react-dom';",
    "import { createPortal } from 'react-dom';\n" + eb_code
)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)
