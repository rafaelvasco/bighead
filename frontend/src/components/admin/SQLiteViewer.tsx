import { useState, useEffect } from "react";
import { api } from "../../services/api";
import type { TableInfo, TableData } from "../../types/admin";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ChevronLeft, ChevronRight, Edit2, Trash2, Save, X } from "lucide-react";

export function SQLiteViewer() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingRow, setEditingRow] = useState<number | null>(null);
  const [editedData, setEditedData] = useState<Record<string, unknown>>({});

  useEffect(() => {
    loadTables();
  }, []);

  useEffect(() => {
    if (selectedTable) {
      loadTableData(selectedTable, currentPage);
    }
  }, [selectedTable, currentPage]);

  const loadTables = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getTables();
      setTables(result.tables);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tables");
    } finally {
      setLoading(false);
    }
  };

  const loadTableData = async (tableName: string, page: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTableData(tableName, page, 20);
      setTableData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load table data");
    } finally {
      setLoading(false);
    }
  };

  const startEditing = (rowIndex: number, row: Record<string, unknown>) => {
    setEditingRow(rowIndex);
    setEditedData({ ...row });
  };

  const cancelEditing = () => {
    setEditingRow(null);
    setEditedData({});
  };

  const saveRow = async () => {
    if (!selectedTable || !tableData || editingRow === null) return;

    const row = tableData.data[editingRow];
    const table = tables.find((t) => t.name === selectedTable);
    const pkColumn = table?.columns.find((c) => c.primary_key);

    if (!pkColumn) {
      setError("No primary key found for this table");
      return;
    }

    const primaryKey = row[pkColumn.name];
    const updates: Record<string, unknown> = {};

    // Only include changed fields
    for (const key in editedData) {
      if (editedData[key] !== row[key] && key !== pkColumn.name) {
        updates[key] = editedData[key];
      }
    }

    if (Object.keys(updates).length === 0) {
      cancelEditing();
      return;
    }

    try {
      await api.updateTableRow(
        selectedTable,
        primaryKey as string | number,
        updates
      );
      cancelEditing();
      loadTableData(selectedTable, currentPage);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update row");
    }
  };

  const deleteRow = async (row: Record<string, unknown>) => {
    if (!selectedTable || !tableData) return;

    const table = tables.find((t) => t.name === selectedTable);
    const pkColumn = table?.columns.find((c) => c.primary_key);

    if (!pkColumn) {
      setError("No primary key found for this table");
      return;
    }

    const primaryKey = row[pkColumn.name];

    if (!confirm("Are you sure you want to delete this row?")) {
      return;
    }

    try {
      await api.deleteTableRow(selectedTable, primaryKey as string | number);
      loadTableData(selectedTable, currentPage);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete row");
    }
  };

  const renderCellValue = (value: unknown): string => {
    if (value === null || value === undefined) return "";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  };

  const formatValue = (value: unknown): string => {
    const str = renderCellValue(value);
    return str.length > 100 ? str.slice(0, 100) + "..." : str;
  };

  if (loading && tables.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Loading tables...
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Tables</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            {tables.map((table) => (
              <Button
                key={table.name}
                onClick={() => {
                  setSelectedTable(table.name);
                  setCurrentPage(1);
                }}
                variant={selectedTable === table.name ? "default" : "outline"}
                className="justify-start"
              >
                <div className="text-left">
                  <div className="font-medium">{table.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {table.row_count} rows, {table.columns.length} columns
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {selectedTable && tableData && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{selectedTable}</CardTitle>
              <div className="text-sm text-muted-foreground">
                Showing {(currentPage - 1) * tableData.per_page + 1} -{" "}
                {Math.min(currentPage * tableData.per_page, tableData.total)} of{" "}
                {tableData.total}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    {tableData.columns.map((col) => (
                      <th
                        key={col}
                        className="text-left p-2 font-medium text-sm bg-muted/50"
                      >
                        {col}
                      </th>
                    ))}
                    <th className="text-left p-2 font-medium text-sm bg-muted/50 w-24">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {tableData.data.map((row, rowIndex) => (
                    <tr key={rowIndex} className="border-b hover:bg-muted/50">
                      {tableData.columns.map((col) => (
                        <td key={col} className="p-2 text-sm">
                          {editingRow === rowIndex ? (
                            <Input
                              value={renderCellValue(editedData[col])}
                              onChange={(e) =>
                                setEditedData({
                                  ...editedData,
                                  [col]: e.target.value,
                                })
                              }
                              className="h-8 text-sm"
                            />
                          ) : (
                            <span className="font-mono text-xs">
                              {formatValue(row[col])}
                            </span>
                          )}
                        </td>
                      ))}
                      <td className="p-2">
                        {editingRow === rowIndex ? (
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={saveRow}
                              className="h-8 w-8 p-0"
                            >
                              <Save className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={cancelEditing}
                              className="h-8 w-8 p-0"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ) : (
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => startEditing(rowIndex, row)}
                              className="h-8 w-8 p-0"
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => deleteRow(row)}
                              className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {tableData.total_pages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <Button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  variant="outline"
                  size="sm"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {currentPage} of {tableData.total_pages}
                </span>
                <Button
                  onClick={() =>
                    setCurrentPage((p) => Math.min(tableData.total_pages, p + 1))
                  }
                  disabled={currentPage === tableData.total_pages}
                  variant="outline"
                  size="sm"
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
