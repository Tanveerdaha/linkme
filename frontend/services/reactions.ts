import api from "@/services/api";
import type { ReactionResult, ReactionSummary } from "@/types";

export async function addPostReaction(postId: string): Promise<ReactionResult> {
  const { data } = await api.post<ReactionResult>(`/posts/${postId}/reaction/`);
  return data;
}

export async function removePostReaction(postId: string): Promise<ReactionResult> {
  const { data } = await api.delete<ReactionResult>(`/posts/${postId}/reaction/`);
  return data;
}

export async function getReactionSummary(postId: string): Promise<ReactionSummary> {
  const { data } = await api.get<ReactionSummary>(`/posts/${postId}/reactions/`);
  return data;
}

export async function addCommentReaction(commentId: string): Promise<ReactionResult> {
  const { data } = await api.post<ReactionResult>(`/comments/${commentId}/reaction/`);
  return data;
}

export async function removeCommentReaction(commentId: string): Promise<ReactionResult> {
  const { data } = await api.delete<ReactionResult>(`/comments/${commentId}/reaction/`);
  return data;
}
