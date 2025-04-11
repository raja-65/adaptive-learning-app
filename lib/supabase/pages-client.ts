import { createServerSideClient } from "@supabase/auth-helpers-nextjs"
import type { GetServerSidePropsContext, NextApiRequest, NextApiResponse } from "next"
import type { Database } from "@/types/supabase"

// For use in getServerSideProps or API routes in the pages/ directory
export function createPagesServerClient(
  context: GetServerSidePropsContext | { req: NextApiRequest; res: NextApiResponse },
) {
  return createServerSideClient<Database>({
    supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL!,
    supabaseKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    cookies: {
      get(name: string) {
        return context.req.cookies[name]
      },
      set(name: string, value: string, options: any) {
        context.res.setHeader(
          "Set-Cookie",
          `${name}=${value}; Path=/; ${options.httpOnly ? "HttpOnly;" : ""} ${
            options.secure ? "Secure;" : ""
          } ${options.maxAge ? `Max-Age=${options.maxAge};` : ""} ${options.domain ? `Domain=${options.domain};` : ""} ${
            options.sameSite ? `SameSite=${options.sameSite};` : ""
          }`,
        )
      },
      remove(name: string, options: any) {
        context.res.setHeader(
          "Set-Cookie",
          `${name}=; Path=/; Max-Age=0; ${options.httpOnly ? "HttpOnly;" : ""} ${options.secure ? "Secure;" : ""} ${
            options.domain ? `Domain=${options.domain};` : ""
          } ${options.sameSite ? `SameSite=${options.sameSite};` : ""}`,
        )
      },
    },
  })
}
</QuickEdit>

Now,
let
's update our middleware to handle both App Router and Pages Router:

```typescriptreact file="middleware.ts"
[v0-no-op-code-block-prefix]
import { createMiddlewareClient } from "@supabase/auth-helpers-nextjs"
import { NextResponse, type NextRequest } from "next/server"

export async function middleware(request: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req: request, res })

  // Check if this is an auth callback
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get("code")

  if (code) {
    // Exchange the code for a session
    await supabase.auth.exchangeCodeForSession(code)
    // Redirect to home page after successful auth
    return NextResponse.redirect(new URL("/", request.url))
  }

  // Refresh session if expired - required for Server Components
  const {
    data: { session },
  } = await supabase.auth.getSession()

  // Get the pathname from the URL
  const path = requestUrl.pathname

  // Auth routes - accessible when not logged in
  const isAuthRoute = path.startsWith("/auth/")

  // Protected routes - require authentication
  const isProtectedRoute = path.startsWith("/student/") || path.startsWith("/professor/")

  // If trying to access protected routes without being logged in
  if (isProtectedRoute && !session) {
    return NextResponse.redirect(new URL("/auth/login", request.url))
  }

  // If logged in and trying to access auth routes
  if (isAuthRoute && session) {
    // Get user role to redirect to appropriate dashboard
    const { data: profile } = await supabase.from("profiles").select("role").eq("id", session.user.id).single()

    if (profile?.role === "professor") {
      return NextResponse.redirect(new URL("/professor/dashboard", request.url))
    } else {
      return NextResponse.redirect(new URL("/student/dashboard", request.url))
    }
  }

  // Role-based access control
  if (session) {
    const { data: profile } = await supabase.from("profiles").select("role").eq("id", session.user.id).single()

    // Prevent students from accessing professor routes
    if (path.startsWith("/professor/") && profile?.role !== "professor") {
      return NextResponse.redirect(new URL("/student/dashboard", request.url))
    }

    // Prevent professors from accessing student routes
    if (path.startsWith("/student/") && profile?.role !== "student") {
      return NextResponse.redirect(new URL("/professor/dashboard", request.url))
    }
  }

  return res
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
}
