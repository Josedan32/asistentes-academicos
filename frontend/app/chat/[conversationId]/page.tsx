import { ChatShell } from "../ChatShell";

export default async function ChatConversationPage({
  params,
}: {
  params: Promise<{ conversationId: string }>;
}) {
  const { conversationId } = await params;
  return <ChatShell initialConversationId={Number(conversationId)} />;
}
