import React from "react";

export default class ChartErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidUpdate(prevProps) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="rounded-lg border border-amber-300/30 bg-amber-400/10 p-5 text-sm leading-6 text-slate-400">
          <p className="font-semibold text-amber-100">Interactive chart unavailable.</p>
          <p className="mt-2">
            The underlying data is still available, but this chart failed to render in the browser. This usually indicates a chart-library runtime issue rather than a missing model result.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
