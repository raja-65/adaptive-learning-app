"use server"

import { createServerActionClient } from "@supabase/auth-helpers-nextjs"
import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { revalidatePath } from "next/cache"
import type { Database } from "@/types/supabase"

type UserRole = "student" | "professor"

export async function signUp(prevState: any, formData: FormData) {
  const email = formData.get("email") as string
  const password = formData.get("password") as string
  const confirmPassword = formData.get("confirmPassword") as string
  const role = formData.get("role") as UserRole
  const fullName = formData.get("fullName") as string

  // Validate inputs
  if (!email || !password || !confirmPassword || !role || !fullName) {
    return { error: "All fields are required" }
  }

  if (password !== confirmPassword) {
    return { error: "Passwords do not match" }
  }

  const cookieStore = cookies()
  const supabase = createServerActionClient<Database>({ cookies: () => cookieStore })

  try {
    // Sign up the user
    const { error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
          role,
        },
      },
    })

    if (signUpError) {
      return { error: signUpError.message }
    }

    // Update the profile with the role
    const { error: profileError } = await supabase
      .from("profiles")
      .update({ role, full_name: fullName })
      .eq("email", email)

    if (profileError) {
      return { error: profileError.message }
    }

    return { success: "Account created successfully. Please check your email for verification." }
  } catch (error) {
    console.error("Sign up error:", error)
    return { error: "An unexpected error occurred. Please try again." }
  }
}

export async function signIn(prevState: any, formData: FormData) {
  const email = formData.get("email") as string
  const password = formData.get("password") as string

  if (!email || !password) {
    return { error: "Email and password are required" }
  }

  const cookieStore = cookies()
  const supabase = createServerActionClient<Database>({ cookies: () => cookieStore })

  try {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      return { error: error.message }
    }

    // Get user role
    const { data: profile } = await supabase.from("profiles").select("role").eq("email", email).single()

    if (profile?.role === "professor") {
      return { success: true, redirectTo: "/professor/dashboard" }
    } else {
      return { success: true, redirectTo: "/student/dashboard" }
    }
  } catch (error) {
    console.error("Login error:", error)
    return { error: "An unexpected error occurred. Please try again." }
  }
}

export async function signOut() {
  const cookieStore = cookies()
  const supabase = createServerActionClient<Database>({ cookies: () => cookieStore })

  await supabase.auth.signOut()
  redirect("/auth/login")
}

export async function updateStudyNodeStatus(nodeId: string, status: "approved" | "rejected") {
  const cookieStore = cookies()
  const supabase = createServerActionClient<Database>({ cookies: () => cookieStore })

  try {
    const { error } = await supabase.from("study_nodes").update({ status }).eq("id", nodeId)

    if (error) {
      return { error: error.message }
    }

    revalidatePath("/professor/dashboard")
    return { success: true }
  } catch (error) {
    console.error("Update node status error:", error)
    return { error: "An unexpected error occurred. Please try again." }
  }
}

export async function updateUserProgress(nodeId: string, status: "not_started" | "in_progress" | "mastered") {
  const cookieStore = cookies()
  const supabase = createServerActionClient<Database>({ cookies: () => cookieStore })

  try {
    const { data: user } = await supabase.auth.getUser()
    if (!user.user) {
      return { error: "User not authenticated" }
    }

    const userId = user.user.id

    // Check if progress record exists
    const { data: existingProgress } = await supabase
      .from("user_progress")
      .select("*")
      .eq("user_id", userId)
      .eq("node_id", nodeId)
      .single()

    if (existingProgress) {
      // Update existing record
      const { error } = await supabase
        .from("user_progress")
        .update({
          status,
          last_accessed: new Date().toISOString(),
        })
        .eq("id", existingProgress.id)

      if (error) {
        return { error: error.message }
      }
    } else {
      // Create new record
      const { error } = await supabase.from("user_progress").insert({
        user_id: userId,
        node_id: nodeId,
        status,
        last_accessed: new Date().toISOString(),
      })

      if (error) {
        return { error: error.message }
      }
    }

    revalidatePath("/student/dashboard")
    revalidatePath(`/student/node/${nodeId}`)
    return { success: true }
  } catch (error) {
    console.error("Update progress error:", error)
    return { error: "An unexpected error occurred. Please try again." }
  }
}

export async function trackInteraction(nodeId: string, interactionType: string, interactionData: any = {}) {
  const cookieStore = cookies()
  const supabase = createServerActionClient<Database>({ cookies: () => cookieStore })

  try {
    const { data: user } = await supabase.auth.getUser()
    if (!user.user) {
      return { error: "User not authenticated" }
    }

    const userId = user.user.id

    const { error } = await supabase.from("user_interactions").insert({
      user_id: userId,
      node_id: nodeId,
      interaction_type: interactionType,
      interaction_data: interactionData,
    })

    if (error) {
      return { error: error.message }
    }

    return { success: true }
  } catch (error) {
    console.error("Track interaction error:", error)
    return { error: "An unexpected error occurred. Please try again." }
  }
}

export async function submitQuizResult(quizId: string, score: number) {
  const cookieStore = cookies()
  const supabase = createServerActionClient<Database>({ cookies: () => cookieStore })

  try {
    const { data: user } = await supabase.auth.getUser()
    if (!user.user) {
      return { error: "User not authenticated" }
    }

    const userId = user.user.id

    // Check if result exists
    const { data: existingResult } = await supabase
      .from("user_quiz_results")
      .select("*")
      .eq("user_id", userId)
      .eq("quiz_id", quizId)
      .single()

    if (existingResult) {
      // Update existing record if new score is better
      if (score > existingResult.score) {
        const { error } = await supabase
          .from("user_quiz_results")
          .update({
            score,
            completed_at: new Date().toISOString(),
          })
          .eq("id", existingResult.id)

        if (error) {
          return { error: error.message }
        }
      }
    } else {
      // Create new record
      const { error } = await supabase.from("user_quiz_results").insert({
        user_id: userId,
        quiz_id: quizId,
        score,
        completed_at: new Date().toISOString(),
      })

      if (error) {
        return { error: error.message }
      }
    }

    // Get the node_id for the quiz
    const { data: quiz } = await supabase.from("quizzes").select("node_id").eq("id", quizId).single()

    if (quiz) {
      // If score is high enough, update progress to mastered
      if (score >= 80) {
        await updateUserProgress(quiz.node_id, "mastered")
      } else if (score >= 50) {
        await updateUserProgress(quiz.node_id, "in_progress")
      }
    }

    return { success: true }
  } catch (error) {
    console.error("Submit quiz result error:", error)
    return { error: "An unexpected error occurred. Please try again." }
  }
}
