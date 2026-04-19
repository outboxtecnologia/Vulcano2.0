import os

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

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

if "class TabelaErrorBoundary" not in code:
    code = code.replace(
        "import React,",
        eb_code + "\nimport React,"
    )

code = code.replace(
    '<TabelaMapaComparativa questor={questorManual} vulcano1={vulcano1} vulcano2={vulcano2} dashboardMeta={dashboardMeta} />',
    '<TabelaErrorBoundary><TabelaMapaComparativa questor={questorManual} vulcano1={vulcano1} vulcano2={vulcano2} dashboardMeta={dashboardMeta} /></TabelaErrorBoundary>'
)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)
