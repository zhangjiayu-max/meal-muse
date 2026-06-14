"use client";

export function CardSkeleton() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-3 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-1/3" />
      <div className="flex items-center gap-6">
        <div className="w-28 h-28 bg-gray-100 rounded-full" />
        <div className="flex-1 space-y-2">
          <div className="h-3 bg-gray-100 rounded w-3/4" />
          <div className="h-3 bg-gray-100 rounded w-1/2" />
          <div className="h-3 bg-gray-100 rounded w-2/3" />
        </div>
      </div>
    </div>
  );
}

export function MealCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-4 animate-pulse">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 bg-gray-100 rounded-lg" />
        <div className="space-y-1">
          <div className="h-3 bg-gray-200 rounded w-12" />
          <div className="h-2 bg-gray-100 rounded w-10" />
        </div>
      </div>
      <div className="py-4 space-y-2">
        <div className="h-3 bg-gray-100 rounded w-3/4" />
        <div className="h-3 bg-gray-100 rounded w-1/2" />
      </div>
    </div>
  );
}

export function ListSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 bg-white rounded-xl border border-gray-100 p-3">
          <div className="w-10 h-10 bg-gray-100 rounded-lg shrink-0" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3 bg-gray-200 rounded w-1/3" />
            <div className="h-2 bg-gray-100 rounded w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-1/4 mb-4" />
      <div className="h-48 bg-gray-50 rounded-lg" />
    </div>
  );
}
