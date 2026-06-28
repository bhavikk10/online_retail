import React from "react";

export default class RouteErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidUpdate(prevProps) {
    if (prevProps.routeKey !== this.props.routeKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="glass rounded-lg p-6">
          <p className="text-lg font-semibold text-red-300">Page render failed.</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            This should not happen in the final dashboard. The error has been caught so the rest of the dashboard remains usable.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
