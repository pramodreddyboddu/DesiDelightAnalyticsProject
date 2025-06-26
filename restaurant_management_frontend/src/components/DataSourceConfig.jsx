import React, { useEffect, useState } from "react";
import { Button } from "./ui/button.jsx";

export default function DataSourceConfig() {
  const [config, setConfig] = useState({ sales: "local", inventory: "local" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/dashboard/data-source-config", { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch config");
        return res.json();
      })
      .then((data) => {
        setConfig(data.data_sources || { sales: "local", inventory: "local" });
        setLoading(false);
      })
      .catch((err) => {
        setError("Failed to load data source config.");
        setLoading(false);
        console.error(err);
      });
  }, []);

  const updateConfig = (type, value) => {
    setConfig((prev) => ({ ...prev, [type]: value }));
  };

  const saveConfig = () => {
    setSaving(true);
    fetch("/api/dashboard/data-source-config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ data_sources: config }),
    })
      .then((res) => res.json())
      .then((data) => {
        setMessage("Configuration updated!");
        setSaving(false);
      })
      .catch(() => {
        setMessage("Failed to update config.");
        setSaving(false);
      });
  };

  const syncClover = (type) => {
    fetch(`/api/clover/sync/${type}`, {
      method: "POST",
      credentials: "include",
    })
      .then((res) => res.json())
      .then(() => setMessage(`${type} sync triggered!`))
      .catch(() => setMessage(`Failed to sync ${type}.`));
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-600">{error}</div>;

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Data Source Configuration</h2>
      <div className="mb-4">
        <label className="mr-2">Sales Source:</label>
        <select
          value={config.sales}
          onChange={(e) => updateConfig("sales", e.target.value)}
        >
          <option value="local">Local</option>
          <option value="clover">Clover</option>
        </select>
        <Button
          className="ml-4"
          onClick={() => syncClover("sales")}
          disabled={config.sales !== "clover"}
        >
          Sync Sales from Clover
        </Button>
      </div>
      <div className="mb-4">
        <label className="mr-2">Inventory Source:</label>
        <select
          value={config.inventory}
          onChange={(e) => updateConfig("inventory", e.target.value)}
        >
          <option value="local">Local</option>
          <option value="clover">Clover</option>
        </select>
        <Button
          className="ml-4"
          onClick={() => syncClover("inventory")}
          disabled={config.inventory !== "clover"}
        >
          Sync Inventory from Clover
        </Button>
      </div>
      <Button onClick={saveConfig} disabled={saving}>
        {saving ? "Saving..." : "Save Configuration"}
      </Button>
      {message && <div className="mt-2 text-green-600">{message}</div>}
    </div>
  );
} 