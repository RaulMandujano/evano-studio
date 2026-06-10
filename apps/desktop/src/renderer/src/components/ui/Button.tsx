import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
}

/** Small reusable button. */
export function Button({ variant = "secondary", className, ...rest }: ButtonProps) {
  return <button className={`btn btn--${variant}${className ? ` ${className}` : ""}`} {...rest} />;
}
