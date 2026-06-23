import clsx from "clsx";
import Badge from "./Badge";

export type TRating = "T-1" | "T-2" | "T-3";

export function tratingVariant(rating: string): "success" | "warning" | "danger" | "neutral" {
  if (rating === "T-1") return "success";
  if (rating === "T-2") return "warning";
  if (rating === "T-3") return "danger";
  return "neutral";
}

export default function TRatingBadge({
  rating,
  className,
  large,
}: {
  rating: string;
  className?: string;
  large?: boolean;
}) {
  return (
    <Badge
      variant={tratingVariant(rating)}
      className={clsx(large && "text-lg px-3 py-1 font-bold", className)}
    >
      {rating}
    </Badge>
  );
}