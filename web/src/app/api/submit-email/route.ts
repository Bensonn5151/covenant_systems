import { NextRequest, NextResponse } from 'next/server';
import { sql } from '@vercel/postgres';

// GET endpoint to view all submitted emails
export async function GET() {
  try {
    // Create table if it doesn't exist
    await sql`
      CREATE TABLE IF NOT EXISTS email_submissions (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) DEFAULT 'New'
      );
    `;

    const { rows } = await sql`
      SELECT id, email, submitted_at, status
      FROM email_submissions
      ORDER BY submitted_at DESC;
    `;

    return NextResponse.json(
      { success: true, emails: rows, count: rows.length },
      { status: 200 }
    );
  } catch (error) {
    console.error('Error fetching emails:', error);
    return NextResponse.json(
      { error: 'Failed to fetch emails' },
      { status: 500 }
    );
  }
}

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

    // Create table if it doesn't exist
    await sql`
      CREATE TABLE IF NOT EXISTS email_submissions (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) DEFAULT 'New'
      );
    `;

    // Insert email into database
    await sql`
      INSERT INTO email_submissions (email, submitted_at, status)
      VALUES (${email}, NOW(), 'New');
    `;

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