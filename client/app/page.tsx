"use client"

import { useEffect, useState } from "react"
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue,} from "@/components/ui/select"
import { Button } from "@/components/ui/button";
import { Mic } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger, DropdownMenuCheckboxItem, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { ChevronDown } from "lucide-react";
import MeetingCard from "@/components/meeting-card";
import { getAudioConfigurations } from '@/lib/api/audio';
import { getMeetings, startMeeting } from '@/lib/api/meeting';
import { getTags } from '@/lib/api/tags';
import { AudioConfig, Tag, Meeting} from '@/lib/api/interface';

// Helper function to filter meetings by status
const filterMeetingsByStatus = (meetings: Meeting[], status: string) => {
  return meetings.filter((meeting) => meeting.status === status);
};

export default function Home() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [audioConfigs, setAudioConfigs] = useState<AudioConfig[]>([]);
  const [selectedAudioId, setSelectedAudioId] = useState<number | null>(null);
  const [meetingTags, setMeetingTags] = useState<Tag[]>([]);
  const [filterTags, setFilterTags] = useState<Tag[]>([]);

  // Run on page load
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const audioOptions = await getAudioConfigurations();
        setAudioConfigs(audioOptions);

        const tags = await getTags();
        setMeetingTags(tags);

        // Loaded after meeting tags
        // const meetingsData = await getMeetings(1, []);
        // setMeetings(meetingsData);
      } catch (error) {
        console.error("Error fetching initial data:", error);
      }
    };

    fetchInitialData();
  }, []);

  const handleSelectChange = (value: string) => {
    setSelectedAudioId(Number(value));
  };

  const handleRecordClick = async () => {
    if (selectedAudioId === null) return;
    try {
      const meeting = await startMeeting(selectedAudioId);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      window.location.href = `/${meeting.meeting_id}`;
    } catch (error) {
      console.error("Error starting meeting:", error);
    }
  };

  const toggleFilterTag = (tag: Tag) => {
    setFilterTags((prev) => {
      const exists = prev.find((t) => t.tag_id === tag.tag_id);
      if (exists) {
        return prev.filter((t) => t.tag_id !== tag.tag_id);
      } else {
        return [...prev, tag];
      }
    });
  };

  const clearFilterTags = () => {
    setFilterTags([]);
  };

  const fetchMeetings = async (errorMessage: string) => {
    try {
      const meetingsData = await getMeetings(1, filterTags.map(tag => tag.name));
      setMeetings(meetingsData);
    } catch (error) {
      console.error(errorMessage, error);
    }
  };

  useEffect(() => {
    fetchMeetings("Error fetching filtered meetings");
  }, [filterTags]);

  const updateMeetings = async () => {
    await fetchMeetings("Error fetching updated meetings");
  };

  return (
    <div className="m-4 w-full h-full">
      <div>
        <h1 className="text-2xl font-bold mb-4">Home</h1>
      </div>
      {/* Top Buttons */}
      <div className="flex justify-between mb-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="flex">
              Filter by tags: {filterTags.length}
              <ChevronDown/>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent >
            {meetingTags.map((tag) => (
              <DropdownMenuCheckboxItem
                key={tag.tag_id}
                checked={filterTags.some((t) => t.tag_id === tag.tag_id)}
                onCheckedChange={() => toggleFilterTag(tag)}
              >
                {tag.name}
              </DropdownMenuCheckboxItem>
            ))}
            <DropdownMenuSeparator />
            <Button
              variant="ghost"
              onClick={clearFilterTags}
            >
              Clear all filters
            </Button>
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="flex space-x-2">
          <Select onValueChange={handleSelectChange}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select an audio option" />
            </SelectTrigger>
            <SelectContent>
              {audioConfigs.map((config) => (
                <SelectItem key={config.audio_id} value={config.audio_id.toString()}>
                  {config.company}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={handleRecordClick}
            disabled={selectedAudioId === null}
            className={`${
            selectedAudioId === null
            ? "bg-gray-400 cursor-not-allowed text-white font-bold"
            : "bg-blue-500 hover:bg-blue-600 text-white font-bold"
            }`}
          >
            <Mic strokeWidth={2.5}/>
            Record
          </Button>
        </div>
      </div>

      {/* Active Meetings */}
      <div className="mb-4">
        <h2 className="text-lg font-bold mb-2">Active Meetings</h2>
        {filterMeetingsByStatus(meetings, "ACTIVE").length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filterMeetingsByStatus(meetings, "ACTIVE").map((meeting) => (
              <MeetingCard
                key={meeting.meeting_id}
                meeting={meeting}
                allTags={meetingTags}
                onUpdateMeetings={updateMeetings}
              />
            ))}
          </div>
        ) : (
          <p>No active meetings found</p>
        )}
      </div>

      {/* Completed Meetings */}
      <div className="mb-4">
        <h2 className="text-lg font-bold mb-2">Completed Meetings</h2>
        {filterMeetingsByStatus(meetings, "COMPLETED").length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filterMeetingsByStatus(meetings, "COMPLETED").map((meeting) => (
              <MeetingCard
                key={meeting.meeting_id}
                meeting={meeting}
                allTags={meetingTags}
                onUpdateMeetings={updateMeetings}
              />
            ))}
          </div>
        ) : (
          <p>No completed meetings found</p>
        )}
      </div>
    </div>
  );
}
