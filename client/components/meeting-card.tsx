import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Clock, Tag as LucideTag, Trash2 } from "lucide-react";
import { formatDistanceToNow, differenceInMinutes, parseISO } from "date-fns";
import { useRouter } from "next/navigation";
import { useState } from "react";
import ActionAlert from "@/components/action-alert";
import { Button } from "@/components/ui/button";
import { deleteTagFromMeeting, addTagToMeeting, stopMeeting, deleteMeeting } from "@/lib/api/meeting";
import { Meeting, Tag } from "@/lib/api/interface";

interface MeetingCardProps {
  meeting: Meeting;
  allTags: Tag[];
  onUpdateMeetings: () => void;
}

// TODO: Add start time and duration formatting

export default function MeetingCard({ meeting, allTags, onUpdateMeetings }: MeetingCardProps) {
  const router = useRouter();
  const isPast = meeting.status === "COMPLETED";

  const [showTagDropdown, setShowTagDropdown] = useState(false);

  const handleMeetingClick = () => {
    router.push(`/${meeting.meeting_id}`);
  };

  const handleTagDelete = async (tagId: number) => {
    try {
      await deleteTagFromMeeting(meeting.meeting_id, tagId);
      // Trigger the callback to update meetings
      onUpdateMeetings();
    } catch (error) {
      console.error("Error deleting tag:", error);
    }
  };

  const handleTagAdd = async (tag: Tag) => {
    try {
      const newTag = await addTagToMeeting(meeting.meeting_id, tag.name);
      onUpdateMeetings();
      setShowTagDropdown(false); // Close dropdown after adding tag
    } catch (error) {
      console.error("Error adding tag:", error);
    }
  };

  const handleStopRecording = async () => {
    try {
      await stopMeeting(meeting.meeting_id);
      onUpdateMeetings();
    } catch (error) {
      console.error("Error stopping recording:", error);
    }
  };

  const handleDeleteMeeting = async () => {
    try {
      await deleteMeeting(meeting.meeting_id);
      onUpdateMeetings();
    } catch (error) {
      console.error("Error deleting meeting:", error);
    }
  };

  const displayDuration = () => {
    const start = new Date(meeting.start_time).getTime();
    const end = new Date(meeting.end_time).getTime();
    const duration = end - start;
    const hours = Math.floor(duration / 3600000);
    const minutes = Math.floor((duration % 3600000) / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    return `${hours} hours, ${minutes} minutes, ${seconds} seconds`
  }

  return (
    <Card className="hover:shadow-md">
      <CardHeader>
        <CardTitle className="text-lg hover:underline" onClick={handleMeetingClick}>{meeting.title}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm">
        {isPast ? (
            <div>
            <p className="line-clamp-2">
              {meeting.summary}
            </p>
            Start Time: {meeting.start_time && new Date(meeting.start_time).toLocaleString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: 'numeric',
              minute: 'numeric',
              second: 'numeric',
              hour12: true,
            })}
            <br />
            Duration: { displayDuration() }
            </div>
        ) : (
          <div>
            Start Time: {meeting.start_time && new Date(meeting.start_time).toLocaleString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: 'numeric',
              minute: 'numeric',
              second: 'numeric',
              hour12: true,
            })}
          </div>
        )}
      </CardContent>
      <CardFooter>
        <div className="flex justify-between w-full">
          <div className="flex gap-1">
            {meeting.tags.map((tag) => (
              <Badge key={tag.tag_id} variant="secondary">
                <LucideTag/>
                {tag.name}
                <button
                  onClick={() => handleTagDelete(tag.tag_id)}
                  className="hover:text-red-500"
                  title="Delete tag"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
                {/* <Button variant="secondary" size="sm" className="hover:text-red-500" onClick={() => handleTagDelete(tag.tag_id)} title="Delete tag">
                  <Trash2 className="h-2 w-2" />
                </Button> */}
              </Badge>
            ))}
            <div className="relative">
              <Button variant="secondary" size="sm" className="hover:bg-green-500" onClick={() => setShowTagDropdown((prev) => !prev)}>
                <Plus />
              </Button>

                {showTagDropdown && (
                <div
                  className="absolute left-full top-0 p-1 border rounded bg-inherit z-10"
                >
                  {allTags
                  .filter((tag) => !meeting.tags.some((t) => t.tag_id === tag.tag_id))
                  .map((tag) => (
                    <div
                    key={tag.tag_id}
                    onClick={() => handleTagAdd(tag)}
                    className="hover:text-green-500 p-1"
                    >
                    {tag.name}
                    </div>
                  ))}
                </div>
                )}
            </div>
          </div>
          <div className="flex gap-2">
            {!isPast ? (
              <ActionAlert
                trigger={
                  <Button variant="secondary" size="sm" className="hover:bg-red-500">
                    Stop Recording
                  </Button>
                }
                title="Stop Recording"
                description="Are you sure you want to stop recording this meeting?"
                actionLabel="Stop"
                onAction={handleStopRecording}
              />
            ) : (
              <ActionAlert
                trigger={
                  <Button variant="secondary" size="sm" className="hover:bg-red-500">
                    Delete Recording
                  </Button>
                }
                title="Delete Meeting"
                description="Are you sure you want to delete this meeting? This action cannot be undone."
                actionLabel="Delete"
                onAction={handleDeleteMeeting}
              />
            )}
          </div>
        </div>
      </CardFooter>
    </Card>
  );
}
