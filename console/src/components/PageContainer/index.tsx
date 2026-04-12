import React from "react";
import { Card, Typography } from "antd";

const { Title, Paragraph } = Typography;

interface PageContainerProps {
  title?: string;
  description?: string;
  extra?: React.ReactNode[];
  children: React.ReactNode;
}

const PageContainer: React.FC<PageContainerProps> = ({
  title,
  description,
  extra,
  children,
}) => {
  return (
    <div style={{ padding: "24px" }}>
      {(title || description || extra) && (
        <div
          style={{
            marginBottom: "24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div style={{ flex: 1 }}>
            {title && (
              <Title level={4} style={{ marginTop: 0, marginBottom: 8 }}>
                {title}
              </Title>
            )}
            {description && (
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                {description}
              </Paragraph>
            )}
          </div>
          {extra && extra.length > 0 && (
            <div style={{ display: "flex", gap: "8px", marginLeft: "16px" }}>
              {extra}
            </div>
          )}
        </div>
      )}
      <Card>{children}</Card>
    </div>
  );
};

export default PageContainer;
