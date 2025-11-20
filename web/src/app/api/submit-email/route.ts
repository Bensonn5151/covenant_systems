import { NextRequest, NextResponse } from 'next/server';
import { writeFile, readFile, mkdir } from 'fs/promises';
import { join } from 'path';

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    if (!email) {
      return NextResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      );
    }

    // Save to JSON file
    const dataDir = join(process.cwd(), 'data');
    const filePath = join(dataDir, 'emails.json');

    try {
      await mkdir(dataDir, { recursive: true });
    } catch (err) {
      // Directory might already exist
    }

    let emails = [];
    try {
      const fileContent = await readFile(filePath, 'utf-8');
      emails = JSON.parse(fileContent);
    } catch (err) {
      // File doesn't exist yet, start with empty array
    }

    // Add new email
    emails.push({
      email,
      submittedAt: new Date().toISOString(),
      status: 'New',
    });

    // Write back to file
    await writeFile(filePath, JSON.stringify(emails, null, 2));

    return NextResponse.json(
      { success: true, message: 'Email submitted successfully' },
      { status: 200 }
    );
  } catch (error) {
    console.error('Error submitting email:', error);
    return NextResponse.json(
      { error: 'Failed to submit email' },
      { status: 500 }
    );
  }
}