/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";

import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import emoji from "remark-emoji";
import rehypeRaw from "rehype-raw";

type MarkdownProps = {
  value: string;
  disabled: boolean;
};

export default function MarkdownWidget({ value, disabled }: MarkdownProps) {
  return (
    <div
      className="form-group mb-3"
      style={{ color: disabled ? "#555" : "#212529" }}
    >
      <ReactMarkdown
        rehypePlugins={[remarkGfm, rehypeHighlight, emoji, rehypeRaw]}
      >
        {value}
      </ReactMarkdown>
    </div>
  );
}
