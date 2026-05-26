import { useState } from "react";
import { Search } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Header } from "@/components/layout/Header";
import { PageHeader } from "@/components/shared/PageHeader";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { useSearchMutation } from "@/services/retrievalApi";
import type { RetrievalResult } from "@/types";

const searchSchema = z.object({
  query: z.string().min(3, "Query must be at least 3 characters"),
});

type SearchFormValues = z.infer<typeof searchSchema>;

export function SearchPage() {
  const [results, setResults] = useState<RetrievalResult[]>([]);
  const [search, { isLoading, error }] = useSearchMutation();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SearchFormValues>({
    resolver: zodResolver(searchSchema),
  });

  const onSubmit = async (values: SearchFormValues) => {
    const result = await search({ query: values.query, top_k: 10 });
    if ("data" in result) {
      setResults(result.data);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <Header
        breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Search" }]}
      />
      <div className="flex-1 overflow-auto p-6 animate-fade-in">
        <div className="mx-auto max-w-2xl space-y-6">
          <PageHeader
            title="Semantic Search"
            description="Search across all processed RFP documents using natural language"
          />

          <form onSubmit={handleSubmit(onSubmit)} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                {...register("query")}
                placeholder="e.g. What are the security requirements?"
                className="pl-9"
              />
            </div>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? <LoadingSpinner size="sm" /> : "Search"}
            </Button>
          </form>

          {errors.query && (
            <p className="text-xs text-destructive">{errors.query.message}</p>
          )}

          {error && (
            <p className="text-xs text-destructive">
              {"message" in error ? error.message : "Search failed"}
            </p>
          )}

          {results.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground">
                {results.length} result{results.length !== 1 ? "s" : ""} found
              </p>
              {results.map((r) => (
                <Card key={r.chunk_id}>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-primary">
                        Score: {(r.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-sm text-foreground leading-relaxed">
                      {r.content}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
