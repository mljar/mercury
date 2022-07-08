import React from "react";

type ProFeatureProps = {
  featureName: string;
};

export default function ProFeatureAlert({ featureName }: ProFeatureProps) {
  return (
    <div style={{ padding: "40px" }}>
      <div className="alert alert-primary mb-3" role="alert">
        <h5>
          <i className="fa fa-info-circle" aria-hidden="true"></i> This is a Pro
          feature{" "}
        </h5>
        You are using an open-source version of the Mercury framework. The{' '} 
        {featureName} is a Pro feature available only for commercial users.
        Please consider purchasing the Mercury commercial license. It is
        perpetual and comes with additional features, dedicated support, and
        allows white-labeling. You can learn more about available licenses on
        our{" "}
        <a href="https://mljar.com/pricing" target="_blank" rel="noreferrer">
          website
        </a>
        .
        <br />
        <br />
        <br />
        <a href="/">
          <i className="fa fa-home" aria-hidden="true" /> Back to home
        </a>
      </div>
    </div>
  );
}
